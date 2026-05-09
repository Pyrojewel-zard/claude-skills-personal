#!/usr/bin/env python3
"""
IEEE Xplore URL Extractor with Pagination Support
使用Playwright模拟浏览器访问IEEE Xplore，提取搜索结果中的所有URL

Usage:
    python ieee_url_extractor.py --url "IEEE_SEARCH_URL" --output "output.json"
    python ieee_url_extractor.py --url "..." --output "output.md" --format markdown
"""

import argparse
import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser


class IEEEURLExtractor:
    """IEEE Xplore URL提取器"""

    def __init__(self, headless: bool = True, rows_per_page: int = 100):
        self.headless = headless
        self.rows_per_page = rows_per_page
        self.results: List[Dict] = []
        self.total_count = 0

    async def extract_paper_info(self, page: Page) -> List[Dict]:
        """从当前页面提取论文信息"""
        papers = []

        # 等待结果加载
        await page.wait_for_selector('.List-results-items .result-item', timeout=30000)

        items = await page.query_selector_all('.List-results-items .result-item')

        for item in items:
            try:
                # 提取标题链接
                title_link = await item.query_selector('h3 a[href*="/document/"]')
                if not title_link:
                    continue

                title = await title_link.inner_text()
                href = await title_link.get_attribute('href')
                arnumber = re.search(r'/document/(\d+)', href or '').group(1) if href else ''

                # 提取年份
                publisher_info = await item.query_selector('.publisher-info-container')
                info_text = await publisher_info.inner_text() if publisher_info else ''
                year_match = re.search(r'Year:\s*(\d{4})', info_text)
                year = year_match.group(1) if year_match else ''

                # 提取作者
                authors = []
                author_links = await item.query_selector_all('.author a[href*="/author/"]')
                for author_link in author_links:
                    author_name = await author_link.inner_text()
                    authors.append(author_name.strip())

                # 提取出版物
                pub_link = await item.query_selector('.description a[href*="/xpl/"]')
                publication = await pub_link.inner_text() if pub_link else ''

                # 提取引用数
                item_text = await item.inner_text()
                cited_match = re.search(r'Cited by:.*?(\d+)', item_text)
                cited_by = cited_match.group(1) if cited_match else '0'

                papers.append({
                    'arnumber': arnumber,
                    'title': title.strip(),
                    'year': year,
                    'authors': authors,
                    'publication': publication.strip(),
                    'cited_by': cited_by,
                    'url': f'https://ieeexplore.ieee.org/document/{arnumber}/'
                })
            except Exception as e:
                print(f"  [Warning] Error extracting paper: {e}")
                continue

        return papers

    async def get_total_count(self, page: Page) -> int:
        """获取总结果数"""
        try:
            count_element = await page.query_selector('.Dashboard-header span')
            if count_element:
                count_text = await count_element.inner_text()
                match = re.search(r'of\s+([\d,]+)\s+results', count_text)
                if match:
                    return int(match.group(1).replace(',', ''))
        except Exception as e:
            print(f"  [Warning] Could not get total count: {e}")
        return 0

    async def build_page_url(self, base_url: str, page_number: int) -> str:
        """构建指定页码的URL"""
        # 解析基础URL并修改分页参数
        url = base_url

        # 移除现有的pageNumber参数
        url = re.sub(r'&pageNumber=\d+', '', url)
        url = re.sub(r'&rowsPerPage=\d+', '', url)

        # 添加新的分页参数
        url = f"{url}&rowsPerPage={self.rows_per_page}&pageNumber={page_number}"

        return url

    async def extract_all_pages(self, url: str, max_pages: Optional[int] = None, start_page: int = 1) -> List[Dict]:
        """提取所有页面的结果"""

        async with async_playwright() as p:
            # 启动浏览器
            print(f"[Info] Launching browser (headless={self.headless})...")
            browser = await p.chromium.launch(headless=self.headless)

            # 创建上下文，模拟真实浏览器
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # 注入脚本隐藏webdriver标识
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = await context.new_page()

            try:
                # 访问起始页
                start_url = await self.build_page_url(url, start_page)
                print(f"[Info] Navigating to: {start_url[:100]}...")
                print(f"[Info] Starting from page {start_page}...")

                await page.goto(start_url, wait_until='networkidle', timeout=60000)

                # 检查是否有验证码或登录页面
                current_url = page.url
                if 'captcha' in current_url.lower() or 'login' in current_url.lower():
                    print("[Warning] Captcha or login page detected!")
                    print("[Info] Please complete the verification in the browser window...")
                    # 等待用户完成验证
                    await page.wait_for_selector('.List-results-items .result-item', timeout=300000)

                # 获取总结果数
                self.total_count = await self.get_total_count(page)
                print(f"[Info] Total results: {self.total_count}")

                if self.total_count == 0:
                    print("[Warning] No results found!")
                    return []

                # 计算总页数
                total_pages = (self.total_count + self.rows_per_page - 1) // self.rows_per_page
                if max_pages:
                    total_pages = min(total_pages, start_page - 1 + max_pages)

                print(f"[Info] Total pages to extract: {total_pages - start_page + 1} (pages {start_page}-{total_pages})")

                # 提取当前页（起始页）
                print(f"[Info] Extracting page {start_page}/{total_pages}...")
                papers = await self.extract_paper_info(page)
                self.results.extend(papers)
                print(f"  Extracted {len(papers)} papers from page {start_page}")

                # 提取剩余页面
                for page_num in range(start_page + 1, total_pages + 1):
                    page_url = await self.build_page_url(url, page_num)
                    print(f"[Info] Extracting page {page_num}/{total_pages}...")

                    await page.goto(page_url, wait_until='networkidle', timeout=60000)

                    # 短暂延迟，避免请求过快
                    await asyncio.sleep(1)

                    papers = await self.extract_paper_info(page)
                    self.results.extend(papers)
                    print(f"  Extracted {len(papers)} papers from page {page_num}")

                print(f"[Info] Total papers extracted: {len(self.results)}")

            except Exception as e:
                print(f"[Error] Extraction failed: {e}")
                raise
            finally:
                await browser.close()

        return self.results

    def save_to_json(self, output_path: str):
        """保存结果到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_date': datetime.now().isoformat(),
                'total_count': self.total_count,
                'extracted_count': len(self.results),
                'papers': self.results
            }, f, ensure_ascii=False, indent=2)
        print(f"[Info] Results saved to JSON: {output_path}")

    def save_to_markdown(self, output_path: str, query_info: str = ""):
        """保存结果到Markdown文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# IEEE Xplore URL List\n\n")
            f.write(f"**Extraction Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Results**: {self.total_count}\n")
            f.write(f"**Extracted Count**: {len(self.results)}\n")
            if query_info:
                f.write(f"**Query**: `{query_info}`\n")
            f.write(f"\n---\n\n")
            f.write("## Papers\n\n")
            f.write("| # | Article Number | Title | Year | Publication | Cited By | URL |\n")
            f.write("|---|----------------|-------|------|-------------|----------|-----|\n")

            for i, paper in enumerate(self.results, 1):
                title = paper['title'].replace('|', '\\|')[:60] + ('...' if len(paper['title']) > 60 else '')
                f.write(f"| {i} | {paper['arnumber']} | {title} | {paper['year']} | {paper['publication'][:30]} | {paper['cited_by']} | [Link]({paper['url']}) |\n")

        print(f"[Info] Results saved to Markdown: {output_path}")

    def save_to_csv(self, output_path: str):
        """保存结果到CSV文件"""
        import csv
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Rank', 'Article Number', 'Title', 'Year', 'Authors', 'Publication', 'Cited By', 'URL'])
            for i, paper in enumerate(self.results, 1):
                writer.writerow([
                    i,
                    paper['arnumber'],
                    paper['title'],
                    paper['year'],
                    '; '.join(paper['authors']),
                    paper['publication'],
                    paper['cited_by'],
                    paper['url']
                ])
        print(f"[Info] Results saved to CSV: {output_path}")


async def main():
    parser = argparse.ArgumentParser(description='IEEE Xplore URL Extractor with Pagination')
    parser.add_argument('--url', required=True, help='IEEE Xplore search URL')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--format', choices=['json', 'markdown', 'csv'], default='markdown', help='Output format')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--visible', action='store_true', help='Run with visible browser (for debugging)')
    parser.add_argument('--rows-per-page', type=int, default=100, help='Results per page (max 100)')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to extract (optional)')
    parser.add_argument('--start-page', type=int, default=1, help='Start from this page number (for resuming)')

    args = parser.parse_args()

    # 创建提取器
    extractor = IEEEURLExtractor(
        headless=not args.visible,
        rows_per_page=args.rows_per_page
    )

    # 提取所有页面
    await extractor.extract_all_pages(args.url, args.max_pages, args.start_page)

    # 保存结果
    if args.format == 'json' or args.output.endswith('.json'):
        extractor.save_to_json(args.output)
    elif args.format == 'csv' or args.output.endswith('.csv'):
        extractor.save_to_csv(args.output)
    else:
        extractor.save_to_markdown(args.output, args.url)

    print(f"\n[Done] Extracted {len(extractor.results)} papers from {extractor.total_count} total results")


if __name__ == '__main__':
    asyncio.run(main())