#!/usr/bin/env python3

import time
import random
import math
import os
import tempfile
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# User agent list for web scraping
USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

def get_driver():
    """Initialize and return Chrome WebDriver"""
    try:
        # Clear WebDriverManager cache
        os.system("rm -rf ~/.wdm/drivers/chromedriver/* 2>/dev/null")
        
        user_agent = random.choice(USER_AGENT_LIST)
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Speed up page loading
        prefs = {
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome WebDriver initialized successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise

def login_to_dice(driver, email: str, password: str) -> bool:
    """Login to Dice.com"""
    try:
        logger.info("Logging into Dice.com")
        driver.get("https://www.dice.com/dashboard/login")
        time.sleep(2)
        
        # Enter email
        email_field = driver.find_element(By.XPATH, '//input[@name="email"]')
        email_field.clear()
        email_field.send_keys(email)
        
        time.sleep(3)
        
        
    
        # Click sign in button
        sign_in_button = driver.find_element(By.XPATH, '//*[@data-testid="sign-in-button"]')
        sign_in_button.click()
        
        
        time.sleep(3)

        # Enter password
        password_field = driver.find_element(By.XPATH, '//input[@name="password"]')
        password_field.clear()
        password_field.send_keys(password)

        # Submit password
        submit_button = driver.find_element(By.XPATH, '//*[@data-testid="submit-password"]')
        submit_button.click()
        time.sleep(2)
        
        # Check if login was successful
        current_url = driver.current_url
        if "login" not in current_url or "dashboard" in current_url or "home-feed" in current_url:
            logger.info("Successfully logged into Dice.com")
            return True
        else:
            logger.error("Failed to login to Dice.com")
            return False
            
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return False

async def get_job_links(email: str, password: str, job_type: str, num_jobs: int, location: str) -> List[str]:
    """Search and collect job links from Dice.com"""
    logger.info(f"Searching for {num_jobs} {job_type} jobs in {location}")
    
    driver = get_driver()
    job_links = []
    
    try:
        # Login first
        if not login_to_dice(driver, email, password):
            return []
        
        # Navigate to job search
        search_url = f"https://www.dice.com/jobs?q={job_type.replace(' ', '%20')}&location={location.replace(' ', '%20').replace(',', '%2C')}"
        driver.get(search_url)
        time.sleep(2)
        
        # Get total job count
        try:
            job_count_element = driver.find_element(By.CSS_SELECTOR, "h4.mobile-job-count-header span[data-cy='search-count-mobile']")
            total_jobs_text = job_count_element.text
            total_jobs = int(total_jobs_text.replace(",", "").strip())
            logger.info(f"Found {total_jobs} total jobs available")
        except Exception:
            total_jobs = num_jobs
            logger.warning("Could not determine total job count, proceeding with requested number")
        
        # Hard-code page limit for consistent scraping
        jobs_per_page = 20
        
        # Iterate through pages using URL pattern
        logger.info("Iterating through pages using URL pattern...")
        page = 1
        max_pages = 10  # Hard-coded to scrape 10 pages consistently
        
        while page <= max_pages:
            page_url = f"{search_url}&page={page}"
            logger.info(f"Scraping page {page}: {page_url}")
            
            driver.get(page_url)
            time.sleep(1)
            
            # Scroll to load content on the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Extract job links from current page
            page_job_links = driver.execute_script("""
                let allLinks = [];
                
                // Try multiple selectors
                let selectors = [
                    'a[data-testid="job-search-job-card-link"]',
                    'a[href*="job-detail"]',
                    'a[data-cy="card-title-link"]',
                    '.card-title-link',
                    '[data-testid="job-card"] a'
                ];
                
                for (let selector of selectors) {
                    let links = Array.from(document.querySelectorAll(selector));
                    if (links.length > 0) {
                        console.log(`Found ${links.length} links with selector: ${selector}`);
                        allLinks = links.map(a => {
                            if (a.href && a.href.includes('job-detail')) {
                                return a.href;
                            }
                            return null;
                        }).filter(link => link);
                        break;
                    }
                }
                
                console.log(`Total job links found on page: ${allLinks.length}`);
                return allLinks;
            """)
            
            # Add unique links from this page
            new_links = 0
            for link in page_job_links:
                if link not in job_links:
                    job_links.append(link)
                    new_links += 1
            
            logger.info(f"Page {page}: Found {len(page_job_links)} links, {new_links} new unique links")
            logger.info(f"Total unique links so far: {len(job_links)}")
            
            # If no new links found, we've reached the end
            if len(page_job_links) == 0:
                logger.info(f"No jobs found on page {page}, stopping pagination")
                break
            
            # Stop if we have enough jobs for efficiency
            if len(job_links) >= num_jobs:
                logger.info(f"Collected enough jobs ({len(job_links)}), stopping pagination")
                break
                
            page += 1
        
        # Remove duplicates and limit to requested number
        unique_links = list(dict.fromkeys(job_links))[:num_jobs]
        logger.info(f"Successfully collected {len(unique_links)} unique job links")
        
        return unique_links
        
    finally:
        driver.quit()

async def apply_to_job(job_type: str, driver, job_url: str, email: str, password: str,
                      resume_path: str, max_attempts: int = 3, skip_login: bool = False) -> dict:
    """Apply to a single job"""
    logger.info(f"Applying to job: {job_url}")
    
    wait = WebDriverWait(driver, 15)
    
    for attempt in range(max_attempts):
        try:
            # Login to Dice only if not already logged in
            if not skip_login:
                logger.info("Logging in for job application")
                if not login_to_dice(driver, email, password):
                    continue
            else:
                logger.info("Skipping login - using existing session")
                # Quick check if we're still logged in by checking current page
                try:
                    current_url = driver.current_url
                    if "login" in current_url.lower():
                        logger.warning("Session expired, re-logging in")
                        if not login_to_dice(driver, email, password):
                            continue
                except Exception:
                    # If we can't check, just try to login
                    logger.warning("Cannot verify session, attempting login")
                    if not login_to_dice(driver, email, password):
                        continue
            
            # Navigate to job posting
            driver.get(job_url)
            time.sleep(3)
            
            # Extract job information
            job_info = extract_job_info(driver)
            
            # Find and click apply button in shadow DOM
            try:
                shadow_host = driver.find_element(By.TAG_NAME, "apply-button-wc")
                time.sleep(2)
                shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
                apply_button = shadow_root.find_element(By.CSS_SELECTOR, ".btn.btn-primary")
                apply_button.click()
                logger.info("Clicked apply button")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Failed to click apply button: {str(e)}")
                continue
            
            # Skip resume upload - let Dice auto-select
            logger.info("Skipping resume upload - using Dice auto-selection")
            
            # Complete application process
            if complete_application(driver, wait):
                result = {
                    "job_link": job_url,
                    "job_type": job_type,
                    "status": "Successful",
                    "time_applied": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    **job_info
                }
                logger.info(f"Successfully applied to job: {job_info.get('job_title', job_type)}")
                return result
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_attempts - 1:
                return {
                    "job_link": job_url,
                    "job_type": job_type,
                    "status": "Failed",
                    "error": str(e),
                    "time_applied": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            continue
    
    return {"status": "Failed", "job_link": job_url, "job_type": job_type}

def extract_job_info(driver) -> dict:
    """Extract job information from the job posting page"""
    job_info = {
        "job_title": None,
        "company": None,
        "job_description": None,
        "posted_date": None
    }
    
    try:
        # Job title
        job_title = driver.find_element(By.CSS_SELECTOR, 'h1[data-cy="jobTitle"]').text
        job_info["job_title"] = job_title
    except Exception:
        logger.warning("Could not extract job title")
    
    try:
        # Company
        company = driver.find_element(By.CSS_SELECTOR, 'li[class*="job-header_jobDetailFirst"]').text
        job_info["company"] = company.strip()
    except Exception:
        logger.warning("Could not extract company name")
    
    try:
        # Job description
        description = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="jobDescriptionHtml"]').text
        job_info["job_description"] = description[:500] + "..." if len(description) > 500 else description
    except Exception:
        logger.warning("Could not extract job description")
    
    return job_info

def upload_resume(driver, resume_path: str, wait: WebDriverWait) -> bool:
    """Handle resume upload process"""
    try:
        logger.info("Starting resume upload process")
        
        # Look for upload button variants
        upload_selectors = [
            "button[data-v-1becdc36]",
            "button[data-v-9fe70a02]",
            "button[contains(text(), 'Upload')]"
        ]
        
        upload_button = None
        for selector in upload_selectors:
            try:
                upload_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                break
            except TimeoutException:
                continue
        
        if not upload_button:
            logger.error("Could not find upload button")
            return False
        
        # Click upload button
        driver.execute_script("arguments[0].click();", upload_button)
        logger.info("Clicked upload button")
        time.sleep(5)
        
        # Find file input
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#fsp-fileUpload")))
        file_input.send_keys(resume_path)
        logger.info(f"Uploaded resume: {resume_path}")
        time.sleep(3)
        
        # Click final upload/confirm button
        final_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.fsp-button.fsp-button--primary.fsp-button-upload"))
        )
        final_button.click()
        logger.info("Confirmed resume upload")
        time.sleep(5)
        
        return True
        
    except Exception as e:
        logger.error(f"Resume upload failed: {str(e)}")
        return False

def complete_application(driver, wait: WebDriverWait) -> bool:
    """Complete the application process after resume upload"""
    try:
        # Click next button
        next_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.seds-button-primary.btn-next"))
        )
        next_button.click()
        logger.info("Clicked next button")
        time.sleep(3)
        
        # Handle work authorization if present
        try:
            work_auth_select = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "workAuthSelect"))
            )
            if work_auth_select.is_displayed():
                select = Select(work_auth_select)
                select.select_by_value("PREFER_NOT_TO_ANSWER")
                logger.info("Handled work authorization question")
                
                # Click next after work auth
                next_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.seds-button-primary.btn-next"))
                )
                next_button.click()
                time.sleep(2)
        except TimeoutException:
            logger.info("No work authorization question found")
        
        # Submit application
        submit_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//button[contains(@class, 'seds-button-primary') and contains(@class, 'btn-next')][contains(., 'Submit')]"
            ))
        )
        submit_button.click()
        logger.info("Submitted application")
        time.sleep(5)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to complete application: {str(e)}")
        return False

# Example usage functions
async def apply_to_single_job(email: str, password: str, job_url: str, resume_path: str, job_type: str = "software developer"):
    """Apply to a single job - standalone function"""
    driver = get_driver()
    try:
        result = await apply_to_job(job_type, driver, job_url, email, password, resume_path)
        return result
    finally:
        driver.quit()

async def apply_to_multiple_jobs(email: str, password: str, job_type: str, num_jobs: int, 
                                location: str, resume_path: str):
    """Apply to multiple jobs - standalone function"""
    # Get job links
    job_links = await get_job_links(email, password, job_type, num_jobs, location)
    
    if not job_links:
        logger.error("No job links found")
        return {"successful": 0, "failed": 0, "total": 0}
    
    successful = 0
    failed = 0
    results = []
    
    for i, job_url in enumerate(job_links, 1):
        logger.info(f"Processing job {i}/{len(job_links)}: {job_url}")
        
        driver = get_driver()
        try:
            result = await apply_to_job(job_type, driver, job_url, email, password, resume_path)
            results.append(result)
            
            if result.get("status") == "Successful":
                successful += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"Error processing job {i}: {str(e)}")
            failed += 1
            results.append({
                "job_link": job_url,
                "status": "Failed",
                "error": str(e)
            })
        finally:
            driver.quit()
        
        # Brief pause between applications
        time.sleep(2)
    
    summary = {
        "successful": successful,
        "failed": failed,
        "total": len(job_links),
        "results": results
    }
    
    logger.info(f"Application summary: {successful} successful, {failed} failed, {len(job_links)} total")
    return summary

if __name__ == "__main__":
    import asyncio
    
    # Example usage
    email = "your-dice-email@example.com"
    password = "your-dice-password"
    resume_path = "/path/to/your/resume.pdf"
    job_type = "python developer"
    location = "San Francisco, CA, USA"
    num_jobs = 5
    
    print("This is the simplified Dice job application module.")
    print("Import this module or use cli.py for actual job applications.")
    print("\nExample usage:")
    print("python cli.py --email your@email.com --resume /path/to/resume.pdf bulk --job-type 'python developer' --num-jobs 5")