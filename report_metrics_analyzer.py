#!/usr/bin/env python3
"""
财务报告类型与GAAP指标关系分析器
分析不同类型的财务报告（10-K、10-Q、13-F等）需要哪些GAAP指标
"""

import os
import xml.etree.ElementTree as ET
import json
from typing import Dict, List, Set, Optional
from collections import defaultdict
import re
from dataclasses import dataclass
from gaap_parser import GAAPParser


@dataclass
class ReportMetric:
    """报告指标关系"""
    metric_name: str
    label: Optional[str]
    role: str
    report_type: str
    frequency: str  # annual, quarterly, etc.
    required: bool = True


class ReportMetricsAnalyzer:
    """财务报告指标分析器"""
    
    def __init__(self, gaap_dir: str):
        self.gaap_dir = gaap_dir
        # 修复GAAPParser中的文件路径
        self.parser = GAAPParser(gaap_dir)
        
        # 检查必要的文件是否存在
        required_files = [
            os.path.join(gaap_dir, 'elts', 'us-gaap-2025.xsd'),
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"警告: 必需文件不存在: {file_path}")
        
        # 报告类型映射表
        self.report_type_mapping = {
            # 10-K相关 (年报)
            'bc': {'type': '10-K', 'section': 'Balance Sheet', 'description': '资产负债表'},
            'ci': {'type': '10-K', 'section': 'Income Statement', 'description': '损益表'},
            'cf': {'type': '10-K', 'section': 'Cash Flow', 'description': '现金流量表'},
            'equity': {'type': '10-K', 'section': 'Equity Statement', 'description': '股东权益变动表'},
            'ap': {'type': '10-K', 'section': 'Accounting Policies', 'description': '会计政策'},
            'debt': {'type': '10-K', 'section': 'Debt Disclosure', 'description': '债务披露'},
            'inv': {'type': '10-K', 'section': 'Investment Disclosure', 'description': '投资披露'},
            'ppe': {'type': '10-K', 'section': 'Property Plant Equipment', 'description': '固定资产'},
            'eps': {'type': '10-K', 'section': 'Earnings Per Share', 'description': '每股收益'},
            'inctax': {'type': '10-K', 'section': 'Income Tax', 'description': '所得税'},
            'lea': {'type': '10-K', 'section': 'Lease', 'description': '租赁'},
            'rd': {'type': '10-K', 'section': 'Research Development', 'description': '研发费用'},
            'se': {'type': '10-K', 'section': 'Subsequent Events', 'description': '期后事项'},
            
            # 10-Q相关 (季报) - 主要是核心财务报表
            'bsoff': {'type': '10-Q', 'section': 'Balance Sheet Summary', 'description': '简化资产负债表'},
            'ni': {'type': '10-Q', 'section': 'Net Income Summary', 'description': '净利润摘要'},
            'ocpfs': {'type': '10-Q', 'section': 'Operating Cash Flow Summary', 'description': '经营现金流摘要'},
            
            # 13-F相关 (机构投资者持仓报告)
            'schedoi-hold': {'type': '13-F', 'section': 'Schedule of Investments Holdings', 'description': '投资持仓明细表'},
            'schedoi-sumhold': {'type': '13-F', 'section': 'Summary Holdings', 'description': '持仓汇总'},
            'schedoi-otsh': {'type': '13-F', 'section': 'Other Securities Held', 'description': '其他持有证券'},
            'schedoi-shorthold': {'type': '13-F', 'section': 'Short Holdings', 'description': '空头持仓'},
            'schedoi-iiaa': {'type': '13-F', 'section': 'Investment Adviser Activities', 'description': '投资顾问活动'},
            'schedoi-oocw': {'type': '13-F', 'section': 'Other Options Contracts Written', 'description': '已售出期权合约'},
            'schedoi-fednote': {'type': '13-F', 'section': 'Federal Note', 'description': '联邦票据'},
            
            # 8-K相关 (重大事件报告)
            'disops': {'type': '8-K', 'section': 'Discontinued Operations', 'description': '终止经营'},
            'reorg': {'type': '8-K', 'section': 'Reorganization', 'description': '重组'},
            'dise': {'type': '8-K', 'section': 'Disposal Events', 'description': '处置事件'},
            
            # 保险公司专用报告
            'fs-ins': {'type': 'Insurance-SAP', 'section': 'Insurance Financial Statements', 'description': '保险财务报表'},
            'fs-mort': {'type': 'Insurance-SAP', 'section': 'Mortgage Insurance', 'description': '抵押保险'},
            
            # 银行专用报告
            'fs-bd': {'type': 'Bank-Call Report', 'section': 'Bank Financial Data', 'description': '银行财务数据'},
            'fs-bt': {'type': 'Bank-Call Report', 'section': 'Bank Trading', 'description': '银行交易'},
            'fs-fhlb': {'type': 'Bank-Call Report', 'section': 'Federal Home Loan Bank', 'description': '联邦住房贷款银行'},
            
            # 投资公司报告
            'invco': {'type': 'Investment Company', 'section': 'Investment Company', 'description': '投资公司'},
            
            # 能源公司专用
            'oi': {'type': 'Energy-Industry', 'section': 'Oil and Gas', 'description': '石油天然气'},
            'regop': {'type': 'Energy-Industry', 'section': 'Regulated Operations', 'description': '监管业务'},
            
            # 医疗保健
            'hco': {'type': 'Healthcare', 'section': 'Healthcare Operations', 'description': '医疗保健业务'},
            
            # 其他特殊披露
            'crcgen': {'type': 'Credit Risk', 'section': 'Credit Risk General', 'description': '信用风险一般披露'},
            'cecl': {'type': 'Credit Risk', 'section': 'Credit Loss', 'description': '信用损失'},
            'fifvd': {'type': 'Fair Value', 'section': 'Fair Value Disclosure', 'description': '公允价值披露'},
            'dr': {'type': 'Derivative', 'section': 'Derivative Risk', 'description': '衍生品风险'},
            'guar': {'type': 'Guarantee', 'section': 'Guarantees', 'description': '担保'},
            'pay': {'type': 'Payment', 'section': 'Payment Systems', 'description': '支付系统'},
        }
        
        # 报告频率映射
        self.frequency_mapping = {
            '10-K': 'Annual',
            '10-Q': 'Quarterly', 
            '8-K': 'Event-based',
            '13-F': 'Quarterly',
            'Insurance-SAP': 'Annual/Quarterly',
            'Bank-Call Report': 'Quarterly',
            'Investment Company': 'Annual/Semi-annual',
            'Energy-Industry': 'Annual',
            'Healthcare': 'Annual',
            'Credit Risk': 'Annual',
            'Fair Value': 'Annual',
            'Derivative': 'Annual',
            'Guarantee': 'Annual',
            'Payment': 'Annual'
        }
        
        # 命名空间
        self.ns = {
            'link': 'http://www.xbrl.org/2003/linkbase',
            'xlink': 'http://www.w3.org/1999/xlink'
        }

    def extract_metrics_from_presentation(self, role_code: str) -> List[str]:
        """从presentation文件中提取指标列表"""
        presentation_file = os.path.join(
            self.gaap_dir, 'dis', f'us-gaap-dis-{role_code}-pre-2025.xml'
        )
        
        metrics = []
        if not os.path.exists(presentation_file):
            return metrics
            
        try:
            tree = ET.parse(presentation_file)
            root = tree.getroot()
            
            # 查找所有loc元素，提取指标名称
            for loc in root.findall('.//link:loc', self.ns):
                href = loc.get(f"{{{self.ns['xlink']}}}href")
                if href and '#us-gaap_' in href:
                    # 提取指标名称
                    metric_name = href.split('#us-gaap_')[1]
                    metrics.append(metric_name)
                    
        except ET.ParseError as e:
            print(f"解析presentation文件错误 {presentation_file}: {e}")
            
        return list(set(metrics))  # 去重

    def analyze_report_metrics(self) -> Dict[str, List[ReportMetric]]:
        """分析所有报告类型的指标关系"""
        report_metrics = defaultdict(list)
        
        for role_code, report_info in self.report_type_mapping.items():
            print(f"分析报告类型: {report_info['type']} - {report_info['description']}")
            
            # 提取该报告类型的指标
            metrics = self.extract_metrics_from_presentation(role_code)
            frequency = self.frequency_mapping.get(report_info['type'], 'Annual')
            
            for metric_name in metrics:
                # 获取指标标签
                label = self.parser.get_label_definition(metric_name)
                
                report_metric = ReportMetric(
                    metric_name=metric_name,
                    label=label,
                    role=role_code,
                    report_type=report_info['type'],
                    frequency=frequency
                )
                
                report_metrics[report_info['type']].append(report_metric)
                
        return dict(report_metrics)

    def generate_report_summary(self, report_metrics: Dict[str, List[ReportMetric]]) -> Dict:
        """生成报告汇总统计"""
        summary = {}
        
        for report_type, metrics in report_metrics.items():
            metric_count = len(metrics)
            unique_metrics = len(set(m.metric_name for m in metrics))
            
            # 按section分组统计
            sections = defaultdict(int)
            for metric in metrics:
                role_info = self.report_type_mapping.get(metric.role, {})
                section = role_info.get('section', 'Unknown')
                sections[section] += 1
            
            summary[report_type] = {
                'total_metrics': metric_count,
                'unique_metrics': unique_metrics,
                'frequency': self.frequency_mapping.get(report_type, 'Unknown'),
                'sections': dict(sections),
                'description': self._get_report_description(report_type)
            }
            
        return summary

    def _get_report_description(self, report_type: str) -> str:
        """获取报告类型描述"""
        descriptions = {
            '10-K': '年度报告 - 公司年度财务报告，包含完整的财务报表和详细披露',
            '10-Q': '季度报告 - 季度财务报告，包含主要财务报表的更新',
            '8-K': '重大事件报告 - 披露重大企业事件和变化',
            '13-F': '机构投资者持仓报告 - 大型机构投资者的持仓披露',
            'Insurance-SAP': '保险公司法定会计报告 - 保险行业专用财务报告',
            'Bank-Call Report': '银行监管报告 - 银行向监管机构提交的财务报告',
            'Investment Company': '投资公司报告 - 共同基金和投资公司的专用报告',
            'Energy-Industry': '能源行业报告 - 石油、天然气等能源公司的专用披露',
            'Healthcare': '医疗保健报告 - 医疗保健行业的专用披露',
            'Credit Risk': '信用风险披露 - 金融机构的信用风险管理披露',
            'Fair Value': '公允价值披露 - 公允价值计量的详细披露',
            'Derivative': '衍生品披露 - 衍生金融工具的风险和使用情况',
            'Guarantee': '担保披露 - 担保义务和或有负债披露',
            'Payment': '支付系统披露 - 支付处理和金融服务披露'
        }
        return descriptions.get(report_type, f'{report_type}相关财务披露')

    def find_common_metrics(self, report_metrics: Dict[str, List[ReportMetric]]) -> Dict:
        """找出不同报告类型之间的共同指标"""
        all_metrics = {}
        for report_type, metrics in report_metrics.items():
            metric_names = set(m.metric_name for m in metrics)
            all_metrics[report_type] = metric_names
            
        # 找出共同指标
        common_analysis = {}
        
        # 10-K和10-Q的共同指标（季报通常是年报的子集）
        if '10-K' in all_metrics and '10-Q' in all_metrics:
            common_10k_10q = all_metrics['10-K'] & all_metrics['10-Q']
            common_analysis['10-K与10-Q共同指标'] = {
                'count': len(common_10k_10q),
                'metrics': list(common_10k_10q)[:10],  # 显示前10个作为示例
                'description': '年报和季报都需要的核心财务指标'
            }
            
        # 所有报告类型的核心共同指标
        if len(all_metrics) > 1:
            core_metrics = set.intersection(*all_metrics.values())
            common_analysis['所有报告共同指标'] = {
                'count': len(core_metrics),
                'metrics': list(core_metrics),
                'description': '所有报告类型都需要的基础指标'
            }
            
        return common_analysis

    def export_to_json(self, data: Dict, filename: str):
        """导出数据到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"数据已导出到: {filename}")

    def generate_detailed_report(self, report_type: str, report_metrics: Dict[str, List[ReportMetric]]) -> Dict:
        """生成特定报告类型的详细分析"""
        if report_type not in report_metrics:
            return {}
            
        metrics = report_metrics[report_type]
        
        # 按section分组
        sections = defaultdict(list)
        for metric in metrics:
            role_info = self.report_type_mapping.get(metric.role, {})
            section = role_info.get('section', 'Unknown')
            sections[section].append({
                'metric_name': metric.metric_name,
                'label': metric.label,
                'role': metric.role
            })
            
        return {
            'report_type': report_type,
            'description': self._get_report_description(report_type),
            'frequency': self.frequency_mapping.get(report_type, 'Unknown'),
            'total_metrics': len(metrics),
            'sections': dict(sections)
        }

    def run_analysis(self) -> Dict:
        """运行完整分析"""
        print("开始分析财务报告类型与GAAP指标关系...")
        
        # 分析所有报告指标
        report_metrics = self.analyze_report_metrics()
        
        # 生成汇总统计
        summary = self.generate_report_summary(report_metrics)
        
        # 分析共同指标
        common_metrics = self.find_common_metrics(report_metrics)
        
        # 组装完整结果
        result = {
            'analysis_date': '2025-01-28',
            'gaap_version': '2025',
            'summary': summary,
            'common_metrics_analysis': common_metrics,
            'detailed_metrics': {}
        }
        
        # 为主要报告类型生成详细分析
        main_reports = ['10-K', '10-Q', '13-F', '8-K']
        for report_type in main_reports:
            if report_type in report_metrics:
                result['detailed_metrics'][report_type] = self.generate_detailed_report(
                    report_type, report_metrics
                )
        
        return result


def main():
    """主函数"""
    # 更新GAAP目录路径
    gaap_dir = "/Users/tingwang/work/gaap-web-service/us-gaap-2025"
    
    if not os.path.exists(gaap_dir):
        print(f"错误: GAAP目录不存在: {gaap_dir}")
        return
        
    # 创建分析器
    analyzer = ReportMetricsAnalyzer(gaap_dir)
    
    try:
        # 运行分析
        result = analyzer.run_analysis()
        
        # 导出结果
        analyzer.export_to_json(result, 'report_metrics_analysis.json')
        
        # 打印汇总信息
        print("\n=== 财务报告类型与GAAP指标关系分析结果 ===")
        print(f"分析日期: {result['analysis_date']}")
        print(f"GAAP版本: {result['gaap_version']}")
        
        print("\n=== 报告类型汇总 ===")
        for report_type, info in result['summary'].items():
            print(f"\n{report_type}:")
            print(f"  描述: {info['description']}")
            print(f"  频率: {info['frequency']}")
            print(f"  总指标数: {info['total_metrics']}")
            print(f"  独特指标数: {info['unique_metrics']}")
            print(f"  涵盖板块: {', '.join(info['sections'].keys())}")
            
        print("\n=== 共同指标分析 ===")
        for analysis_type, info in result['common_metrics_analysis'].items():
            print(f"\n{analysis_type}:")
            print(f"  数量: {info['count']}")
            print(f"  说明: {info['description']}")
            if info['count'] > 0:
                print(f"  示例指标: {', '.join(info['metrics'][:5])}...")
                
        print(f"\n详细分析结果已保存到: report_metrics_analysis.json")
        
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()