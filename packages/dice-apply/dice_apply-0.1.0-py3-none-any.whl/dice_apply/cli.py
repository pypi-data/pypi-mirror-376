#!/usr/bin/env python3

import argparse
import asyncio
import getpass
import os
import sys
import time
from pathlib import Path

# Import core functions from core module
from .core import get_job_links, apply_to_job, get_driver, apply_to_multiple_jobs as apply_multiple

async def apply_to_single_job(email: str, password: str, job_url: str, resume_path: str = None, job_type: str = "software developer"):
    """Apply to a single job"""
    print(f"🎯 Applying to job: {job_url}")
    
    # Validate resume path if provided
    if resume_path and not os.path.exists(resume_path):
        print(f"❌ Resume file not found: {resume_path}")
        return False
    
    driver = get_driver()
    try:
        # For single job application, we need to mock the resume_url since the original
        # function expects a Supabase URL. We'll modify this to work with local files.
        result = await apply_to_job(
            job_type=job_type,
            driver=driver,
            job_url=job_url,
            email=email,
            password=password,
            resume_path=resume_path,  # Pass local path directly
            max_attempts=3
        )
        
        if result and result.get("status") == "Successful":
            print(f"✅ Successfully applied to: {job_url}")
            return True
        else:
            print(f"❌ Failed to apply to: {job_url}")
            return False
            
    finally:
        driver.quit()

async def apply_to_multiple_jobs(email: str, password: str, job_type: str, num_jobs: int, location: str, resume_path: str = None):
    """Apply to multiple jobs with single persistent session"""
    print(f"🔍 Searching for {num_jobs} {job_type} jobs in {location}")

    if resume_path and not os.path.exists(resume_path):
        print(f"❌ Resume file not found: {resume_path}")
        return

    # Get job links
    job_links = await get_job_links(email, password, job_type, num_jobs, location)
    print(f"📋 Found {len(job_links)} job opportunities")

    successful = 0
    failed = 0

    # Create single driver session for all applications
    driver = get_driver()
    logged_in = False

    try:
        for i, job_url in enumerate(job_links, 1):
            print(f"\n💼 Processing job {i}/{len(job_links)}")

            try:
                result = await apply_to_job(
                    job_type=job_type,
                    driver=driver,
                    job_url=job_url,
                    email=email,
                    password=password,
                    resume_path=resume_path,
                    max_attempts=3,
                    skip_login=logged_in  # Skip login after first successful login
                )

                # Mark as logged in after first application attempt (successful or not)
                if not logged_in:
                    logged_in = True

                if result and result.get("status") == "Successful":
                    successful += 1
                    print(f"✅ Success! Applied to: {result.get('job_title', job_type)}")
                else:
                    failed += 1
                    print(f"❌ Failed to apply to job")

            except Exception as e:
                failed += 1
                print(f"❌ Error applying to job: {str(e)}")

            # Brief pause between applications
            time.sleep(2)

    finally:
        # Close driver only once at the end
        driver.quit()

    print(f"\n🎉 Application Summary:")
    print(f"✅ Successful applications: {successful}")
    print(f"❌ Failed applications: {failed}")
    print(f"📊 Total processed: {len(job_links)}")

def main():
    parser = argparse.ArgumentParser(description="Dice Job Application CLI Tool")
    parser.add_argument("--email", default="samatcrispy@gmail.com", help="Your Dice.com email")
    parser.add_argument("--password", default="0ldSp!ce", help="Your Dice.com password (will prompt if not provided)")
    parser.add_argument("--resume", help="Path to your resume file (PDF, DOC, DOCX) - optional, Dice can auto-select")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Single job application
    single_parser = subparsers.add_parser("apply", help="Apply to a single job")
    single_parser.add_argument("job_url", help="Direct URL to the job posting")
    single_parser.add_argument("--job-type", default="software developer", help="Job type/title")
    
    # Multiple job applications
    bulk_parser = subparsers.add_parser("bulk", help="Apply to multiple jobs")
    bulk_parser.add_argument("--job-type", default="software developer", help="Type of job to search for")
    bulk_parser.add_argument("--num-jobs", type=int, default=10, help="Number of jobs to apply to")
    bulk_parser.add_argument("--location", default="San Francisco, CA, USA", help="Job location")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Get password if not provided
    password = args.password or getpass.getpass("Enter your Dice.com password: ")
    
    # Validate resume file if provided
    resume_path = None
    if args.resume:
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"❌ Resume file not found: {resume_path}")
            return
        
        if resume_path.suffix.lower() not in ['.pdf', '.doc', '.docx']:
            print("❌ Resume must be PDF, DOC, or DOCX format")
            return
    
    print(f"🤖 Dice Job Application Tool")
    print(f"📧 Email: {args.email}")
    print(f"📄 Resume: Auto-selected by Dice (upload skipped)")
    
    try:
        if args.command == "apply":
            print(f"🎯 Single Job Application Mode")
            asyncio.run(apply_to_single_job(
                email=args.email,
                password=password,
                job_url=args.job_url,
                resume_path=str(resume_path) if resume_path else None,
                job_type=args.job_type
            ))
        
        elif args.command == "bulk":
            print(f"🚀 Bulk Application Mode")
            result = asyncio.run(apply_multiple(
                email=args.email,
                password=password,
                job_type=args.job_type,
                num_jobs=args.num_jobs,
                location=args.location,
                resume_path=None
            ))
            
            # Print summary
            print(f"\n🎉 Application Summary:")
            print(f"✅ Successful applications: {result.get('successful', 0)}")
            print(f"❌ Failed applications: {result.get('failed', 0)}")
            print(f"📊 Total processed: {result.get('total', 0)}")
    
    except KeyboardInterrupt:
        print("\n⏹️  Application process interrupted by user")
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()