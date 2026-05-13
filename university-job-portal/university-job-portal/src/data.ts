// data.ts — Types only. All data is now fetched live from the FastAPI backend.

export interface Country {
  code: string;
  name: string;
}

export interface University {
  id: string;
  name: string;
  countryCode: string;
}

export interface JobPosting {
  id: string;
  title: string;
  department: string;
  type: string;
  location: string;
}

export const API_BASE = "http://localhost:8000/api";
