#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Chrome浏览器自动下载PDF，绕过Sci-Hub反爬
遇到人机验证时可手动处理，脚本会自动等待
"""

import os
import csv
import time
import re
from pathlib import Path
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 配置
SCI_HUB_URL = "https://sci-hub.ru"
OUTPUT_DIR = Path("/tmp/scihub_downloads")
DELAY_BETWEEN_DOWNLOADS = 5  # 秒，避免操作太快被封
MAX_WAIT_TIME = 30  # 秒，页面加载和用户手动验证的最大等待时间

def sanitize_filename(doi):
    """将DOI转换为合法的文件名"""
    return doi.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_') + ".pdf"

def init_chrome():
    """初始化Chrome浏览器，使用用户现有配置，避免重复登录验证"""
    chrome_options = Options()

    # 设置下载目录，自动下载不询问
    prefs = {
        "download.default_directory": str(OUTPUT_DIR.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,  # 禁用安全浏览检查，避免PDF被拦截
        "plugins.always_open_pdf_externally": True,  # 直接下载PDF而不是在浏览器中打开
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # 禁用自动化检测特征
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # 启动浏览器
    driver = webdriver.Chrome(options=chrome_options)

    # 移除webdriver特征，避免反爬检测
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def wait_for_download_complete(driver, expected_filename, timeout=30):
    """等待文件下载完成"""
    start_time = time.time()
    download_path = OUTPUT_DIR / expected_filename

    while time.time() - start_time < timeout:
        if download_path.exists() and not download_path.name.endswith('.crdownload'):
            return True
        time.sleep(1)
    return False

def download_pdf_from_doi(driver, doi, title):
    """从DOI下载PDF"""
    try:
        filename = sanitize_filename(doi)
        output_path = OUTPUT_DIR / filename

        # 如果文件已经存在，跳过
        if output_path.exists():
            print(f"✅ 已存在，跳过: {filename}")
            return True

        # 打开Sci-Hub页面
        url = f"{SCI_HUB_URL}/{quote(doi)}"
        driver.get(url)

        # 等待页面加载完成
        WebDriverWait(driver, MAX_WAIT_TIME).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # 检查是否有Cloudflare验证或人机验证
        if "Cloudflare" in driver.title or "验证" in driver.page_source or "captcha" in driver.page_source.lower():
            print("⚠️  需要人机验证，请在浏览器中完成验证，脚本会自动继续...")
            # 等待用户完成验证，直到页面加载完成
            WebDriverWait(driver, 300).until(  # 5分钟等待时间让用户手动验证
                lambda d: "Cloudflare" not in d.title and "验证" not in d.page_source
            )
            print("✅ 验证通过，继续下载...")
            time.sleep(2)

        # 尝试查找下载链接
        pdf_url = None

        # 方法1: 查找embed/iframe的src
        try:
            embed = driver.find_element(By.TAG_NAME, "embed")
            pdf_url = embed.get_attribute("src")
        except NoSuchElementException:
            pass

        if not pdf_url:
            try:
                iframe = driver.find_element(By.TAG_NAME, "iframe")
                pdf_url = iframe.get_attribute("src")
            except NoSuchElementException:
                pass

        # 方法2: 查找包含save/下载的按钮
        if not pdf_url:
            try:
                save_button = driver.find_element(By.XPATH, "//a[contains(text(), 'save') or contains(text(), '下载') or contains(@onclick, 'location.href')]")
                onclick = save_button.get_attribute("onclick")
                match = re.search(r"location.href\s*=\s*'([^']+)'", onclick)
                if match:
                    pdf_url = match.group(1)
                else:
                    pdf_url = save_button.get_attribute("href")
            except NoSuchElementException:
                pass

        # 方法3: 从页面中提取PDF链接
        if not pdf_url:
            page_source = driver.page_source
            match = re.search(r'window\.location\s*=\s*"([^"]+\.pdf[^"]*)"', page_source)
            if match:
                pdf_url = match.group(1)
            else:
                match = re.search(r'src=["\']([^"\']+\.pdf[^"\']*)["\']', page_source)
                if match:
                    pdf_url = match.group(1)

        if not pdf_url:
            print(f"❌ 找不到PDF下载链接: {doi}")
            return False

        # 处理相对URL
        if pdf_url.startswith('//'):
            pdf_url = 'https:' + pdf_url
        elif not pdf_url.startswith('http'):
            from urllib.parse import urljoin
            pdf_url = urljoin(SCI_HUB_URL, pdf_url)

        print(f"🔍 找到PDF链接: {pdf_url[:80]}...")

        # 下载PDF，如果是直接的PDF链接，直接打开就会自动下载
        if '.pdf' in pdf_url:
            driver.get(pdf_url)
            # 等待下载完成
            if wait_for_download_complete(driver, filename):
                # 有时候下载的文件名可能不是我们期望的，需要检查并重命名
                # 查找最新下载的PDF文件
                pdf_files = list(OUTPUT_DIR.glob("*.pdf"))
                if pdf_files:
                    latest_pdf = max(pdf_files, key=os.path.getctime)
                    # 如果文件名和预期的不一样，重命名
                    if latest_pdf.name != filename:
                        latest_pdf.rename(output_path)
                return True
            else:
                print(f"❌ 下载超时: {doi}")
                return False
        else:
            # 如果不是直接的PDF链接，尝试点击下载按钮
            try:
                driver.execute_script(f"window.open('{pdf_url}', '_blank');")
                time.sleep(3)
                # 切换到新标签页
                driver.switch_to.window(driver.window_handles[-1])
                # 等待下载开始
                time.sleep(5)
                # 关闭新标签页
                driver.close()
                # 切换回原标签页
                driver.switch_to.window(driver.window_handles[0])

                # 等待下载完成
                if wait_for_download_complete(driver, filename):
                    return True
                else:
                    return False
            except Exception as e:
                print(f"❌ 下载失败: {str(e)[:50]}...")
                return False

    except Exception as e:
        print(f"❌ 处理失败 {doi}: {str(e)[:80]}...")
        return False

def main():
    # 创建输出目录
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    csv_path = Path("/tmp/doi_2021_and_earlier.csv")
    if not csv_path.exists():
        print(f"❌ 错误：DOI文件 {csv_path} 不存在")
        return

    # 初始化Chrome
    print("🚀 启动Chrome浏览器...")
    driver = init_chrome()
    driver.maximize_window()

    # 先访问Sci-Hub首页，让用户提前处理可能的验证
    print("🔗 访问Sci-Hub首页，如有验证请手动完成...")
    driver.get(SCI_HUB_URL)
    time.sleep(5)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            total = len(rows)
            print(f"📚 共 {total} 篇论文需要下载")

            for i, row in enumerate(rows, 1):
                doi = row['DOI'].strip()
                title = row['Title']
                item_key = row['Item Key']

                if not doi:
                    skipped_count += 1
                    continue

                filename = sanitize_filename(doi)
                output_path = OUTPUT_DIR / filename

                if output_path.exists():
                    print(f"[{i}/{total}] ✅ 已下载，跳过: {doi}")
                    skipped_count += 1
                    continue

                print(f"\n[{i}/{total}] 正在处理: {doi}")
                print(f"标题: {title[:80]}...")

                # 下载PDF，最多重试2次
                download_success = False
                for retry in range(2):
                    if download_pdf_from_doi(driver, doi, title):
                        download_success = True
                        break
                    print(f"🔄 第 {retry+1} 次重试...")
                    time.sleep(2)

                if download_success:
                    print(f"✅ 下载成功: {filename}")
                    success_count += 1
                else:
                    print(f"❌ 下载失败: {doi}")
                    failed_count += 1

                # 每10篇输出一次统计
                if i % 10 == 0:
                    print(f"\n===== 进度 {i}/{total} | 成功: {success_count} | 失败: {failed_count} | 跳过: {skipped_count} =====\n")

                # 间隔时间，避免操作太快
                time.sleep(DELAY_BETWEEN_DOWNLOADS)

    finally:
        # 关闭浏览器
        print("\n\n🏁 全部任务完成！")
        print(f"总论文数: {total}")
        print(f"成功下载: {success_count}")
        print(f"失败: {failed_count}")
        print(f"跳过: {skipped_count}")
        print(f"成功率: {success_count / (total - skipped_count) * 100:.1f}%")
        print(f"PDF保存目录: {OUTPUT_DIR}")

        # 询问用户是否关闭浏览器
        try:
            input("按回车键关闭浏览器...")
        except:
            pass
        driver.quit()

if __name__ == "__main__":
    main()
