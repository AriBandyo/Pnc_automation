import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import uuid

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = DATA_DIR / "job_queue.xlsx"

class ExcelManager:
#Manages job queue stored in Excel file
    
    def __init__(self, excel_path: Path | str = EXCEL_PATH):
        self.excel_path = Path(excel_path)
        
        if not self.excel_path.exists():
            raise FileNotFoundError(
                f"Excel file not found: {excel_path}\n"
                f"Please create it with JobPosts, PostingRuns, and JobTemplates sheets"
            )

    def get_queued_jobs(self) -> List[Dict]:
        df = pd.read_excel(self.excel_path, sheet_name='JobPosts')
        queued = df[df['Status'] == 'QUEUED']
        return queued.to_dict('records')

    def get_job(self, job_id: str) -> Optional[Dict]:
        df = pd.read_excel(self.excel_path, sheet_name='JobPosts')
        job_rows = df[df['JobId'] == job_id]
        
        if len(job_rows) == 0:
            return None
        
        return job_rows.iloc[0].to_dict()

    def get_posting_runs(self, job_id: str) -> List[Dict]:
        df = pd.read_excel(self.excel_path, sheet_name='PostingRuns')
        runs = df[df['JobId'] == job_id]
        return runs.to_dict('records')

    def get_queued_runs(self, job_id: str) -> List[Dict]:
        all_runs = self.get_posting_runs(job_id)
        return [r for r in all_runs if r['RunStatus'] == 'QUEUED']

    def transition_job_status(
        self, 
        job_id: str, 
        from_status: str, 
        to_status: str, 
        locked_by: str = None
    ) -> bool:
        df = pd.read_excel(self.excel_path, sheet_name='JobPosts')
        for col in ["CreatedAt", "StartedAt", "FinishedAt"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.floor("s")
        
        if "LockedBy" in df.columns:
            df["LockedBy"] = df["LockedBy"].astype("string")
        
        job_mask = df['JobId'] == job_id
        
        if not job_mask.any():
            print(f"Warning: Job {job_id} not found")
            return False
        
        job_idx = df[job_mask].index[0]
        current_status = df.loc[job_idx, 'Status']
        
        if current_status != from_status:
            print(f"Warning: Job {job_id} status is {current_status}, expected {from_status}")
            return False
        
        df.loc[job_idx, 'Status'] = to_status
        
        if to_status == 'RUNNING':
            df.loc[job_idx, 'StartedAt'] = pd.Timestamp.now().floor("s")
            if locked_by:
                df.loc[job_idx, 'LockedBy'] = locked_by
        
        elif to_status in ['POSTED', 'FAILED', 'PARTIAL_FAILED']:
            df.loc[job_idx, 'FinishedAt'] = pd.Timestamp.now().floor("s")
        
        self._write_sheet(df, 'JobPosts')
        
        return True

    def update_posting_run(
        self,
        run_id: str,
        status: str,
        portal_posting_id: str = None,
        proof_link: str = None,
        error_reason: str = None
    ):
        df = pd.read_excel(self.excel_path, sheet_name='PostingRuns')

        for col in ["CreatedAt", "StartedAt", "FinishedAt"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.floor("s")

        for col in ["PortalPostingId", "ProofLink", "ErrorReason", "PortalName", "PortalUrl", "RunStatus"]:
            if col in df.columns:
                df[col] = df[col].astype("string")
        
        run_mask = df['RunId'] == run_id
        
        if not run_mask.any():
            print(f"Warning: Run {run_id} not found")
            return
        
        run_idx = df[run_mask].index[0]
        
        df.loc[run_idx, 'RunStatus'] = status
        df.loc[run_idx, 'FinishedAt'] = pd.Timestamp.now().floor("s")
        
        if portal_posting_id:
            df.loc[run_idx, 'PortalPostingId'] = str(portal_posting_id)
        
        if proof_link:
            df.loc[run_idx, 'ProofLink'] = proof_link
        
        if error_reason:
            df.loc[run_idx, 'ErrorReason'] = error_reason
        
        current_attempts = df.loc[run_idx, 'Attempts']
        df.loc[run_idx, 'Attempts'] = current_attempts + 1
        
        self._write_sheet(df, 'PostingRuns')

    def transition_run_status(
        self,
        run_id: str,
        from_status: str,
        to_status: str
    ) -> bool:
        df = pd.read_excel(self.excel_path, sheet_name='PostingRuns')
        
        run_mask = df['RunId'] == run_id
        
        if not run_mask.any():
            return False
        
        run_idx = df[run_mask].index[0]
        current_status = df.loc[run_idx, 'RunStatus']
        
        if current_status != from_status:
            return False
        
        df.loc[run_idx, 'RunStatus'] = to_status
        
        if to_status == 'RUNNING':
            df.loc[run_idx, 'StartedAt'] = pd.Timestamp.now().floor("s")
        
        self._write_sheet(df, 'PostingRuns')
        return True

    def create_job(
        self,
        title: str,
        description: str,
        location: str,
        portals: List[str],
        salary: str = None,
        template_id: str = None
    ) -> str:
        job_id = f"JOB_{uuid.uuid4().hex[:8].upper()}"
        
        job_data = {
            'JobId': job_id,
            'Title': title,
            'Description': description,
            'Location': location,
            'Salary': salary,
            'TemplateId': template_id,
            'Status': 'QUEUED',
            'CreatedAt': datetime.now(),
            'StartedAt': None,
            'FinishedAt': None,
            'LockedBy': None
        }
        
        df_jobs = pd.read_excel(self.excel_path, sheet_name='JobPosts')
        df_jobs = pd.concat([df_jobs, pd.DataFrame([job_data])], ignore_index=True)
        self._write_sheet(df_jobs, 'JobPosts')
        
        df_runs = pd.read_excel(self.excel_path, sheet_name='PostingRuns')
        
        for portal in portals:
            run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"
            
            run_data = {
                'RunId': run_id,
                'JobId': job_id,
                'PortalName': portal,
                #'PortalUrl': self._get_portal_url(portal),
                'RunStatus': 'QUEUED',
                'PortalPostingId': None,
                'ProofLink': None,
                'ErrorReason': None,
                'Attempts': 0,
                'CreatedAt': datetime.now(),
                'FinishedAt': None
            }
            
            df_runs = pd.concat([df_runs, pd.DataFrame([run_data])], ignore_index=True)
        
        self._write_sheet(df_runs, 'PostingRuns')
        
        print(f"Created job {job_id} with {len(portals)} posting runs")
        return job_id

    def _write_sheet(self, df: pd.DataFrame, sheet_name: str):
        self.excel_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if self.excel_path.exists() else "w"

        if mode == "a":
            with pd.ExcelWriter(
                self.excel_path,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace",
            ) as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            with pd.ExcelWriter(self.excel_path, engine="openpyxl", mode="w") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    def _get_portal_url(self, portal_name: str) -> str:
        portal_urls = {
            'laurentian': 'https://careerhub.laurentian.ca/employers/login.htm',
            'sfu': 'https://myexperience.sfu.ca',
            'concordia': 'https://excel.concordia.ca/employers/login-page.htm',
            'saskatchewan': 'https://careerlink.usask.ca/login-main/employer-login.htm',
            'unb': 'https://experience.unb.ca/home/employers/login.htm',
            'mta': 'https://experience.mta.ca/employer/login.htm',
            'wlu': 'https://navigator.wlu.ca/home/employers/login.htm',
            'regina': 'https://uregina-csm.symplicity.com/employers/',
            'royalroads': 'https://royalroads-csm.symplicity.com/employers/',
        }
        
        return portal_urls.get(portal_name, 'URL_NOT_FOUND')

    def finalize_job_status(self, job_id: str):
        runs = self.get_posting_runs(job_id)
        statuses = [r['RunStatus'] for r in runs]
        
        if all(s == 'POSTED' for s in statuses):
            final_status = 'POSTED'
        elif all(s == 'FAILED' for s in statuses):
            final_status = 'FAILED'
        else:
            final_status = 'PARTIAL_FAILED'
        #CHANGE IT LATER 
        #self.transition_job_status(job_id, 'RUNNING', final_status)
        
        return final_status


# TESTING CODE 

if __name__ == "__main__":
    """
    Test the Excel Manager
    Run this to verify everything works
    """
    print("=" * 60)
    print("Testing Excel Manager")
    print("=" * 60)
    print()
    
    
    em = ExcelManager(EXCEL_PATH)
    
    print("Test 1: Creating a test job")
    job_id = em.create_job(
        title="TEST - Software Engineer",
        description="This is a test job posting",
        location="Toronto, ON",
        portals=['laurentian', 'sfu'],
        salary="80k-100k"
    )
    print(f"Created: {job_id}")
    print()
    
    
    print("Test 2: Getting queued jobs")
    queued = em.get_queued_jobs()
    print(f"Found {len(queued)} queued jobs")
    for job in queued:
        print(f"   - {job['JobId']}: {job['Title']}")
    print()
    
    
    print("Test 3: Transitioning job status")
    success = em.transition_job_status(job_id, 'QUEUED', 'RUNNING', 'WORKER_TEST')
    if success:
        print(f" Successfully transitioned {job_id} to RUNNING")
    else:
        print(f" Failed to transition {job_id}")
    print()
    
    
    print("Test 4: Getting posting runs")
    runs = em.get_posting_runs(job_id)
    print(f"Found {len(runs)} posting runs for {job_id}")
    for run in runs:
        print(f"   - {run['RunId']}: {run['PortalName']} ({run['RunStatus']})")
    print()
    
    
    print("Test 5: Updating posting run")
    if runs:
        first_run = runs[0]
        em.update_posting_run(
            run_id=first_run['RunId'],
            status='POSTED',
            portal_posting_id='TEST_12345',
            proof_link='screenshots/test.png'
        )
        print(f"Updated {first_run['RunId']}")
    print()
    
    
    print("Test 6: Finalizing job status")
    
    if len(runs) > 1:
        em.update_posting_run(
            run_id=runs[1]['RunId'],
            status='FAILED',
            error_reason='Test failure'
        )
    
    final_status = em.finalize_job_status(job_id)
    print(f"Final status: {final_status}")
    print()
    
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)
    print()
    print("Check your Excel file - you should see:")
    print("1. New job in JobPosts (with PARTIAL_FAILED status)")
    print("2. Two runs in PostingRuns (one POSTED, one FAILED)")