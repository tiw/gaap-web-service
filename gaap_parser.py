import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set
import os
import re

class GAAPParser:
    def __init__(self, gaap_dir: str):
        self.gaap_dir = gaap_dir
        self.label_file = os.path.join(gaap_dir, 'elts', 'us-gaap-lab-2025.xml')
        self.ref_file = os.path.join(gaap_dir, 'elts', 'us-gaap-ref-2025.xml')
        self.xsd_file = os.path.join(gaap_dir, 'elts', 'us-gaap-2025.xsd')
        
        # 命名空间
        self.ns = {
            'link': 'http://www.xbrl.org/2003/linkbase',
            'xlink': 'http://www.w3.org/1999/xlink',
            'ref': 'http://www.xbrl.org/2006/ref',
            'codification-part': 'http://fasb.org/codification-part/2025'
        }
        
    def get_all_element_names(self) -> List[str]:
        """获取所有GAAP元素名称"""
        try:
            with open(self.xsd_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用正则表达式查找所有元素名称
            pattern = r"<link:loc xlink:href='#us-gaap_([A-Za-z0-9]+)'"
            matches = re.findall(pattern, content)
            
            # 去重并排序
            unique_elements = sorted(list(set(matches)))
            return unique_elements
        except Exception as e:
            print(f"Error reading XSD file: {e}")
            return []
        
    def get_label_definition(self, element_name: str) -> Optional[str]:
        """获取元素的英文标签定义"""
        try:
            tree = ET.parse(self.label_file)
            root = tree.getroot()
            
            # 查找对应的标签
            loc_xpath = f".//link:loc[@xlink:href='us-gaap-2025.xsd#us-gaap_{element_name}']"
            loc_elements = root.findall(loc_xpath, self.ns)
            
            if not loc_elements:
                # 尝试不带us-gaap_前缀的查找
                loc_xpath = f".//link:loc[@xlink:href='us-gaap-2025.xsd#{element_name}']"
                loc_elements = root.findall(loc_xpath, self.ns)
                
            if not loc_elements:
                return None
                
            loc_element = loc_elements[0]
            label_id = loc_element.get(f"{{{self.ns['xlink']}}}label")
            
            # 查找对应的标签文本
            label_text_xpath = f".//link:label[@xlink:label='{label_id}']"
            label_elements = root.findall(label_text_xpath, self.ns)
            
            # 如果没找到，尝试查找labelArc关联的标签
            if not label_elements:
                label_arc_xpath = f".//link:labelArc[@xlink:from='{label_id}']"
                label_arc_elements = root.findall(label_arc_xpath, self.ns)
                if label_arc_elements:
                    to_label_id = label_arc_elements[0].get(f"{{{self.ns['xlink']}}}to")
                    label_elements = root.findall(f".//link:label[@xlink:label='{to_label_id}']", self.ns)
            
            if label_elements:
                return label_elements[0].text
                
            return None
        except Exception as e:
            print(f"Error parsing label file: {e}")
            return None
            
    def get_reference_standards(self, element_name: str) -> List[Dict[str, str]]:
        """获取元素的参考标准"""
        references = []
        try:
            tree = ET.parse(self.ref_file)
            root = tree.getroot()
            
            # 查找对应的参考文献链接
            loc_xpath = f".//link:loc[@xlink:href='us-gaap-2025.xsd#us-gaap_{element_name}']"
            loc_elements = root.findall(loc_xpath, self.ns)
            
            if not loc_elements:
                # 尝试不带us-gaap_前缀的查找
                loc_xpath = f".//link:loc[@xlink:href='us-gaap-2025.xsd#{element_name}']"
                loc_elements = root.findall(loc_xpath, self.ns)
            
            if not loc_elements:
                return references
                
            loc_element = loc_elements[0]
            loc_label = loc_element.get(f"{{{self.ns['xlink']}}}label")
            
            # 查找关联的参考文献
            arc_xpath = f".//link:referenceArc[@xlink:from='{loc_label}']"
            arc_elements = root.findall(arc_xpath, self.ns)
            
            for arc_element in arc_elements:
                ref_label = arc_element.get(f"{{{self.ns['xlink']}}}to")
                
                # 查找参考文献详情
                ref_xpath = f".//link:reference[@xlink:label='{ref_label}']"
                ref_elements = root.findall(ref_xpath, self.ns)
                
                for ref_element in ref_elements:
                    ref_info = {}
                    
                    # 获取URI
                    uri_element = ref_element.find(".//codification-part:URI", self.ns)
                    if uri_element is not None:
                        ref_info['uri'] = uri_element.text
                        
                    # 获取主题和子主题
                    topic_element = ref_element.find(".//codification-part:Topic", self.ns)
                    if topic_element is not None:
                        ref_info['topic'] = topic_element.text
                        
                    subtopic_element = ref_element.find(".//codification-part:SubTopic", self.ns)
                    if subtopic_element is not None:
                        ref_info['subtopic'] = subtopic_element.text
                        
                    # 获取章节和段落
                    section_element = ref_element.find(".//ref:Section", self.ns)
                    if section_element is not None:
                        ref_info['section'] = section_element.text
                        
                    paragraph_element = ref_element.find(".//ref:Paragraph", self.ns)
                    if paragraph_element is not None:
                        ref_info['paragraph'] = paragraph_element.text
                        
                    if ref_info:
                        references.append(ref_info)
                        
            return references
        except Exception as e:
            print(f"Error parsing reference file: {e}")
            return references
            
    def get_element_info(self, element_name: str) -> Dict[str, any]:
        """获取元素的完整信息"""
        result = {
            'element_name': element_name,
            'label': self.get_label_definition(element_name),
            'references': self.get_reference_standards(element_name)
        }
        return result