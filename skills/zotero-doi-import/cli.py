#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zotero文献管理工具
支持读取文献列表、管理分类等功能
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class ZoteroManager:
    """Zotero API管理类"""
    
    def __init__(self, user_id: Optional[str] = None, api_key: Optional[str] = None):
        """
        初始化Zotero管理器
        
        Args:
            user_id: Zotero用户ID
            api_key: Zotero API密钥
        """
        self.base_url = "https://api.zotero.org"
        self.user_id = user_id or os.getenv('ZOTERO_USER_ID') or ""
        self.api_key = api_key or os.getenv('ZOTERO_API_KEY') or ""
        self.timeout = float(os.getenv('ZOTERO_HTTP_TIMEOUT', '20'))
        
        if not self.user_id or not self.api_key:
            print("错误：请设置ZOTERO_USER_ID和ZOTERO_API_KEY环境变量，或在初始化时提供参数")
            print("您可以在这里获取：https://www.zotero.org/settings/keys")
            return
            
        # 基础请求头
        self.headers = {
            'Zotero-API-Version': '3',
            'Zotero-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': f'zotero-llm-classify/1.0 (user {self.user_id})'
        }
        
        # 构建带重试的Session
        self.session = requests.Session()
        retry_config = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET", "POST", "DELETE", "PATCH"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_config)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        print(f"已连接到用户 {self.user_id} 的Zotero库")
    
    def get_library_info(self) -> Dict[str, Any]:
        """获取库信息"""
        try:
            url = f"{self.base_url}/keys/{self.api_key}"
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取库信息失败：{e}")
            return {}
    
    def get_items(self, limit: int = 50, start: int = 0) -> List[Dict[str, Any]]:
        """
        获取文献列表
        
        Args:
            limit: 限制返回数量（最大100）
            start: 起始位置
            
        Returns:
            文献列表
        """
        try:
            url = f"{self.base_url}/users/{self.user_id}/items"
            params = {
                'limit': min(limit, 100),
                'start': start,
                'format': 'json'
            }
            
            response = self.session.get(url, headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            items = response.json()
            print(f"成功获取 {len(items)} 条文献记录")
            return items
            
        except requests.exceptions.RequestException as e:
            print(f"获取文献列表失败：{e}")
            return []
    
    def get_collections(self) -> List[Dict[str, Any]]:
        """
        获取所有分类（集合）
        
        Returns:
            分类列表
        """
        try:
            url = f"{self.base_url}/users/{self.user_id}/collections"
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            collections = response.json()
            print(f"成功获取 {len(collections)} 个分类")
            return collections
            
        except requests.exceptions.RequestException as e:
            print(f"获取分类列表失败：{e}")
            return []
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """
        获取所有标签
        
        Returns:
            标签列表
        """
        try:
            url = f"{self.base_url}/users/{self.user_id}/tags"
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            tags = response.json()
            print(f"成功获取 {len(tags)} 个标签")
            return tags
            
        except requests.exceptions.RequestException as e:
            print(f"获取标签列表失败：{e}")
            return []
    
    def display_items(self, items: List[Dict[str, Any]], limit: int = 10):
        """
        显示文献列表
        
        Args:
            items: 文献列表
            limit: 显示数量限制
        """
        print(f"\n=== 文献列表 (显示前{min(limit, len(items))}条) ===")
        
        for i, item in enumerate(items[:limit]):
            data = item.get('data', {})
            title = data.get('title', '无标题')
            item_type = data.get('itemType', '未知类型')
            creators = data.get('creators', [])
            date = data.get('date', '未知日期')
            
            # 获取作者信息
            authors = []
            for creator in creators:
                if 'firstName' in creator and 'lastName' in creator:
                    authors.append(f"{creator['firstName']} {creator['lastName']}")
                elif 'name' in creator:
                    authors.append(creator['name'])
            
            author_str = ', '.join(authors) if authors else '未知作者'
            
            print(f"\n{i+1}. 【{item_type}】 {title}")
            print(f"   作者: {author_str}")
            print(f"   日期: {date}")
            print(f"   ID: {data.get('key', 'N/A')}")
    
    def display_collections(self, collections: List[Dict[str, Any]]):
        """
        显示分类列表（按层级结构显示）
        
        Args:
            collections: 分类列表
        """
        print(f"\n=== 分类列表 ===")
        
        # 创建父子关系映射
        parent_child_map = {}
        root_collections = []
        all_collections = {}
        
        # 建立集合索引和父子关系
        for collection in collections:
            data = collection.get('data', {})
            key = data.get('key')
            parent_key = data.get('parentCollection')
            all_collections[key] = collection
            
            if parent_key:
                if parent_key not in parent_child_map:
                    parent_child_map[parent_key] = []
                parent_child_map[parent_key].append(key)
            else:
                root_collections.append(key)
        
        def print_collection_tree(collection_key, level=0):
            """递归打印分类树"""
            if collection_key not in all_collections:
                return
                
            collection = all_collections[collection_key]
            data = collection.get('data', {})
            name = data.get('name', '未命名分类')
            
            indent = "  " * level
            if level > 0:
                indent += "└─ "
            
            # 找到在原列表中的序号
            original_index = next((i for i, c in enumerate(collections) if c['data']['key'] == collection_key), -1)
            print(f"{original_index + 1}. {indent}{name} (ID: {collection_key})")
            
            # 递归打印子分类
            if collection_key in parent_child_map:
                for child_key in sorted(parent_child_map[collection_key]):
                    print_collection_tree(child_key, level + 1)
        
        # 按名称排序根分类，然后打印
        root_collections_with_names = []
        for root_key in root_collections:
            if root_key in all_collections:
                name = all_collections[root_key]['data']['name']
                root_collections_with_names.append((name, root_key))
        
        # 按名称排序
        root_collections_with_names.sort(key=lambda x: x[0])
        
        # 打印根分类及其子分类
        for name, root_key in root_collections_with_names:
            print_collection_tree(root_key)
    
    def display_tags(self, tags: List[Dict[str, Any]], limit: int = 20):
        """
        显示标签列表
        
        Args:
            tags: 标签列表
            limit: 显示数量限制
        """
        print(f"\n=== 标签列表 (显示前{min(limit, len(tags))}个) ===")
        
        for i, tag_info in enumerate(tags[:limit]):
            if isinstance(tag_info, dict):
                tag_name = tag_info.get('tag', '未知标签')
                num_items = tag_info.get('meta', {}).get('numItems', 0)
                print(f"{i+1}. {tag_name} ({num_items}个文献)")
            else:
                print(f"{i+1}. {tag_info}")
    
    def search_items(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索文献
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            搜索结果列表
        """
        try:
            url = f"{self.base_url}/users/{self.user_id}/items"
            params = {
                'q': query,
                'qmode': 'everything',
                'limit': min(limit, 100),
                'format': 'json'
            }
            
            response = self.session.get(url, headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            items = response.json()
            print(f"搜索 '{query}' 找到 {len(items)} 条结果")
            return items
            
        except requests.exceptions.RequestException as e:
            print(f"搜索失败：{e}")
            return []
    
    def get_items_by_collection(self, collection_key: str, limit: int = 50, start: int = 0) -> List[Dict[str, Any]]:
        """
        获取指定分类下的文献

        Args:
            collection_key: 分类ID
            limit: 返回数量限制
            start: 起始偏移

        Returns:
            文献列表
        """
        try:
            url = f"{self.base_url}/users/{self.user_id}/collections/{collection_key}/items"
            params = {
                'limit': min(limit, 100),
                'start': start,
                'format': 'json'
            }

            response = self.session.get(url, headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()

            items = response.json()
            print(f"分类 {collection_key} 第 {start+1} - {start+len(items)} 条文献，共 {len(items)} 条")
            return items

        except requests.exceptions.RequestException as e:
            print(f"获取分类文献失败：{e}")
            return []
    
    def get_item_detail(self, item_key: str) -> Dict[str, Any]:
        """
        获取文献详细信息
        
        Args:
            item_key: 文献ID
            
        Returns:
            文献详细信息
        """
        try:
            url = f"{self.base_url}/users/{self.user_id}/items/{item_key}"
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            item = response.json()
            return item
            
        except requests.exceptions.RequestException as e:
            print(f"获取文献详情失败：{e}")
            return {}

    def delete_item(self, item_key: str, version: int = None) -> bool:
        """
        删除指定的文献条目

        Args:
            item_key: 文献ID
            version: 条目版本号（如果未提供将自动获取）

        Returns:
            是否成功
        """
        try:
            # 如果没有提供版本号，先获取当前版本
            if version is None:
                item_detail = self.get_item_detail(item_key)
                if not item_detail:
                    print(f"❌ 无法获取文献详情: {item_key}")
                    return False
                version = item_detail.get('version', 0)

            url = f"{self.base_url}/users/{self.user_id}/items/{item_key}"

            # 添加版本号到请求头
            headers = self.headers.copy()
            headers['If-Unmodified-Since-Version'] = str(version)

            response = self.session.delete(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            print(f"✅ 成功删除文献: {item_key}")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ 删除文献失败：{e}")
            return False
    
    def add_item_to_collection(self, item_key: str, collection_key: str) -> bool:
        """
        将文献添加到指定分类
        
        Args:
            item_key: 文献ID
            collection_key: 分类ID
            
        Returns:
            是否成功
        """
        try:
            # 先获取文献的当前信息
            item = self.get_item_detail(item_key)
            if not item:
                return False
            
            # 获取当前的分类列表
            current_collections = item.get('data', {}).get('collections', [])
            
            # 检查是否已经在该分类中
            if collection_key in current_collections:
                print(f"文献已经在分类 {collection_key} 中")
                return True
            
            # 添加新分类
            updated_collections = current_collections + [collection_key]
            
            # 准备更新数据
            update_data = {
                "collections": updated_collections
            }
            
            # 使用PATCH方法更新
            url = f"{self.base_url}/users/{self.user_id}/items/{item_key}"
            headers = self.headers.copy()
            headers['If-Unmodified-Since-Version'] = str(item.get('version', 0))
            
            response = self.session.patch(url, headers=headers, json=update_data, timeout=self.timeout)
            response.raise_for_status()
            
            print(f"✅ 成功将文献添加到分类 {collection_key}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 添加文献到分类失败：{e}")
            return False
    
    def remove_item_from_collection(self, item_key: str, collection_key: str) -> bool:
        """
        从指定分类中移除文献
        
        Args:
            item_key: 文献ID
            collection_key: 分类ID
            
        Returns:
            是否成功
        """
        try:
            # 先获取文献的当前信息
            item = self.get_item_detail(item_key)
            if not item:
                return False
            
            # 获取当前的分类列表
            current_collections = item.get('data', {}).get('collections', [])
            
            # 检查是否在该分类中
            if collection_key not in current_collections:
                print(f"文献不在分类 {collection_key} 中")
                return True
            
            # 移除分类
            updated_collections = [c for c in current_collections if c != collection_key]
            
            # 准备更新数据
            update_data = {
                "collections": updated_collections
            }
            
            # 使用PATCH方法更新
            url = f"{self.base_url}/users/{self.user_id}/items/{item_key}"
            headers = self.headers.copy()
            headers['If-Unmodified-Since-Version'] = str(item.get('version', 0))
            
            response = self.session.patch(url, headers=headers, json=update_data, timeout=self.timeout)
            response.raise_for_status()
            
            print(f"✅ 成功从分类 {collection_key} 中移除文献")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 从分类中移除文献失败：{e}")
            return False
    
    def create_collection(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新的分类
        
        Args:
            collection_data: 分类数据，包含name和可选的parentCollection
            
        Returns:
            创建的分类信息
        """
        try:
            url = f"{self.base_url}/users/{self.user_id}/collections"
            
            response = self.session.post(url, headers=self.headers, json=[collection_data], timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if result and 'successful' in result and result['successful']:
                # Zotero API返回的successful是字典，键是索引
                successful_items = result['successful']
                if successful_items:
                    # 获取第一个成功创建的项目
                    first_key = list(successful_items.keys())[0]
                    created_collection = successful_items[first_key]
                    print(f"✅ 成功创建分类: {collection_data['name']}")
                    return created_collection
                else:
                    print(f"❌ 创建分类失败: successful字段为空")
                    return {}
            elif result and 'failed' in result and result['failed']:
                failed_items = result['failed']
                if failed_items:
                    first_key = list(failed_items.keys())[0]
                    failed_info = failed_items[first_key]
                    print(f"❌ 创建分类失败: {failed_info}")
                else:
                    print(f"❌ 创建分类失败: 未知错误")
                return {}
            else:
                print(f"❌ 创建分类失败，未知响应格式: {result}")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 创建分类失败：{e}")
            return {}
    
    def delete_collection(self, collection_key: str, version: int = None) -> bool:
        """
        删除指定的分类
        
        Args:
            collection_key: 分类ID
            version: 分类版本号（如果提供）
            
        Returns:
            是否成功
        """
        try:
            # 如果没有提供版本号，先获取当前版本
            if version is None:
                collection_detail = self.get_collection_detail(collection_key)
                if not collection_detail:
                    print(f"❌ 无法获取分类详情: {collection_key}")
                    return False
                version = collection_detail.get('version', 0)
            
            url = f"{self.base_url}/users/{self.user_id}/collections/{collection_key}"
            
            # 添加版本号到请求头
            headers = self.headers.copy()
            headers['If-Unmodified-Since-Version'] = str(version)
            
            response = self.session.delete(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            print(f"✅ 成功删除分类: {collection_key}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 删除分类失败：{e}")
            return False
    
    def get_collection_detail(self, collection_key: str) -> Dict[str, Any]:
        """
        获取分类详细信息
        
        Args:
            collection_key: 分类ID
            
        Returns:
            分类详细信息
        """
        try:
            url = f"{self.base_url}/users/{self.user_id}/collections/{collection_key}"
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            collection = response.json()
            return collection
            
        except requests.exceptions.RequestException as e:
            print(f"获取分类详情失败：{e}")
            return {}
    
    def manage_item_collections_interactive(self):
        """交互式管理文献分类"""
        print("\n=== 文献分类管理 ===")
        
        # 获取文献列表
        items = self.get_items(limit=10)
        if not items:
            print("无法获取文献列表")
            return
        
        print("\n选择要管理的文献：")
        self.display_items(items, limit=10)
        
        try:
            item_choice = input("\n请输入文献序号 (1-10): ").strip()
            item_index = int(item_choice) - 1
            
            if item_index < 0 or item_index >= len(items):
                print("无效的文献序号")
                return
            
            selected_item = items[item_index]
            item_key = selected_item['data']['key']
            item_title = selected_item['data'].get('title', '无标题')
            
            print(f"\n选择的文献: {item_title}")
            print(f"文献ID: {item_key}")
            
            # 获取文献详细信息
            item_detail = self.get_item_detail(item_key)
            if item_detail:
                current_collections = item_detail.get('data', {}).get('collections', [])
                print(f"当前所在分类: {len(current_collections)} 个")
                
                # 显示当前分类
                if current_collections:
                    all_collections = self.get_collections()
                    collection_map = {c['data']['key']: c['data']['name'] for c in all_collections}
                    for coll_key in current_collections:
                        coll_name = collection_map.get(coll_key, '未知分类')
                        print(f"  - {coll_name} (ID: {coll_key})")
            
            # 获取所有分类
            collections = self.get_collections()
            if not collections:
                print("无法获取分类列表")
                return
            
            print(f"\n=== 操作选项 ===")
            print("1. 添加到分类")
            print("2. 从分类中移除")
            print("0. 返回")
            
            action = input("\n请选择操作: ").strip()
            
            if action == '1':
                # 添加到分类
                print("\n选择要添加到的分类：")
                self.display_collections(collections)
                
                choice_input = input("\n请输入分类序号或分类ID: ").strip()
                collection_key = self._parse_collection_choice(choice_input, collections)
                
                if collection_key:
                    self.add_item_to_collection(item_key, collection_key)
                    
            elif action == '2':
                # 从分类中移除
                if not current_collections:
                    print("该文献不在任何分类中")
                    return
                
                print("\n该文献所在的分类：")
                all_collections = self.get_collections()
                collection_map = {c['data']['key']: c['data']['name'] for c in all_collections}
                
                for i, coll_key in enumerate(current_collections):
                    coll_name = collection_map.get(coll_key, '未知分类')
                    print(f"{i+1}. {coll_name} (ID: {coll_key})")
                
                choice_input = input("\n请输入要移除的分类序号或分类ID: ").strip()
                
                try:
                    choice_num = int(choice_input)
                    if 1 <= choice_num <= len(current_collections):
                        collection_key = current_collections[choice_num - 1]
                    else:
                        print("序号超出范围")
                        return
                except ValueError:
                    collection_key = choice_input
                
                if collection_key in current_collections:
                    self.remove_item_from_collection(item_key, collection_key)
                else:
                    print("无效的分类ID")
                    
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            print("\n操作已取消")
    
    def _parse_collection_choice(self, choice_input: str, collections: List[Dict[str, Any]]) -> str:
        """解析分类选择输入"""
        try:
            choice_num = int(choice_input)
            if 1 <= choice_num <= len(collections):
                return collections[choice_num - 1]['data']['key']
            else:
                print(f"序号超出范围，请输入1-{len(collections)}之间的数字")
                return ""
        except ValueError:
            # 直接返回输入的分类ID
            return choice_input
    
    def analyze_library(self):
        """分析库的整体情况"""
        print("\n=== 正在分析您的Zotero库 ===")
        
        # 获取基本信息
        items = self.get_items(limit=100)
        collections = self.get_collections()
        tags = self.get_tags()
        
        if not items:
            print("无法获取文献信息")
            return
        
        # 统计文献类型
        item_types = {}
        for item in items:
            item_type = item.get('data', {}).get('itemType', '未知')
            item_types[item_type] = item_types.get(item_type, 0) + 1
        
        print(f"\n=== 库统计信息 ===")
        print(f"文献总数: {len(items)}")
        print(f"分类数量: {len(collections)}")
        print(f"标签数量: {len(tags)}")
        
        print(f"\n=== 文献类型分布 ===")
        for item_type, count in sorted(item_types.items(), key=lambda x: x[1], reverse=True):
            print(f"{item_type}: {count}篇")
    
    def test_baseline_functionality(self):
        """测试Baseline功能：将第一个文献添加到指定分类"""
        print("\n=== 测试Baseline功能 ===")
        print("这将演示如何将第一个文献添加到某个分类中")
        
        # 获取第一个文献
        items = self.get_items(limit=1)
        if not items:
            print("❌ 无法获取文献列表")
            return
        
        first_item = items[0]
        item_key = first_item['data']['key']
        item_title = first_item['data'].get('title', '无标题')
        
        print(f"\n选择的文献: {item_title}")
        print(f"文献ID: {item_key}")
        
        # 获取分类列表
        collections = self.get_collections()
        if not collections:
            print("❌ 无法获取分类列表")
            return
        
        print(f"\n可用的分类:")
        self.display_collections(collections)
        
        # 让用户选择分类
        choice_input = input(f"\n请选择要添加到的分类 (序号1-{len(collections)}或分类ID): ").strip()
        
        if not choice_input:
            print("操作已取消")
            return
        
        collection_key = self._parse_collection_choice(choice_input, collections)
        
        if not collection_key:
            print("❌ 无效的分类选择")
            return
        
        # 获取分类名称
        selected_collection = None
        for coll in collections:
            if coll['data']['key'] == collection_key:
                selected_collection = coll
                break
        
        if selected_collection:
            collection_name = selected_collection['data']['name']
            print(f"\n准备将文献 '{item_title}' 添加到分类 '{collection_name}'")
            
            confirm = input("确认执行吗？(y/N): ").strip().lower()
            if confirm == 'y':
                success = self.add_item_to_collection(item_key, collection_key)
                if success:
                    print(f"\n🎉 Baseline测试成功！")
                    print(f"文献 '{item_title}' 已成功添加到分类 '{collection_name}'")
                else:
                    print(f"\n❌ Baseline测试失败")
            else:
                print("操作已取消")
        else:
            print("❌ 找不到指定的分类")


def main():
    """主函数"""
    print("Zotero文献管理工具")
    print("=" * 50)
    
    # 检查环境变量
    user_id = os.getenv('ZOTERO_USER_ID')
    api_key = os.getenv('ZOTERO_API_KEY')
    
    if not user_id or not api_key:
        print("\n请先设置环境变量：")
        print("export ZOTERO_USER_ID='你的用户ID'")
        print("export ZOTERO_API_KEY='你的API密钥'")
        print("\n或者可以在代码中直接指定：")
        print("zotero = ZoteroManager(user_id='你的用户ID', api_key='你的API密钥')")
        print("\n获取API密钥：https://www.zotero.org/settings/keys")
        return
    
    # 创建Zotero管理器
    zotero = ZoteroManager()
    
    try:
        # 显示菜单
        while True:
            print(f"\n=== 主菜单 ===")
            print("1. 显示文献列表")
            print("2. 显示分类列表")
            print("3. 显示标签列表")
            print("4. 搜索文献")
            print("5. 查看指定分类下的文献")
            print("6. 管理文献分类 ⭐")
            print("7. 分析库统计")
            print("8. 获取库信息")
            print("9. 测试Baseline功能")
            print("0. 退出")
            
            choice = input("\n请选择操作 (0-9): ").strip()
            
            if choice == '0':
                print("再见！")
                break
            elif choice == '1':
                items = zotero.get_items(limit=20)
                zotero.display_items(items)
            elif choice == '2':
                collections = zotero.get_collections()
                zotero.display_collections(collections)
            elif choice == '3':
                tags = zotero.get_tags()
                zotero.display_tags(tags)
            elif choice == '4':
                query = input("请输入搜索关键词: ").strip()
                if query:
                    results = zotero.search_items(query)
                    zotero.display_items(results)
            elif choice == '5':
                collections = zotero.get_collections()
                if collections:
                    zotero.display_collections(collections)
                    choice_input = input("\n请输入分类序号或分类ID: ").strip()
                    if choice_input:
                        # 尝试将输入解析为序号
                        try:
                            choice_num = int(choice_input)
                            if 1 <= choice_num <= len(collections):
                                collection_key = collections[choice_num - 1]['data']['key']
                                collection_name = collections[choice_num - 1]['data']['name']
                                print(f"选择的分类: {collection_name} (ID: {collection_key})")
                            else:
                                print(f"序号超出范围，请输入1-{len(collections)}之间的数字")
                                continue
                        except ValueError:
                            # 如果不是数字，就当作分类ID处理
                            collection_key = choice_input
                            print(f"使用分类ID: {collection_key}")
                        
                        items = zotero.get_items_by_collection(collection_key)
                        zotero.display_items(items)
            elif choice == '6':
                zotero.manage_item_collections_interactive()
            elif choice == '7':
                zotero.analyze_library()
            elif choice == '8':
                info = zotero.get_library_info()
                print(f"\n=== 库信息 ===")
                print(json.dumps(info, indent=2, ensure_ascii=False))
            elif choice == '9':
                zotero.test_baseline_functionality()
            else:
                print("无效选择，请重试")
    
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"程序出错：{e}")


if __name__ == "__main__":
    main() 