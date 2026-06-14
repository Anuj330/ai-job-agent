export type JobSource = "naukri" | "linkedin" | "bayt" | "indeed";

export interface JobListing {
  id: string;
  title: string;
  company: string;
  location: string | null;
  source: JobSource | string;
  source_url: string;
  apply_url: string | null;
  description: string | null;
  experience_level: string | null;
  experience_min_years: number | null;
  experience_max_years: number | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  work_mode: "remote" | "hybrid" | "onsite" | null;
  visa_sponsorship: boolean | null;
  skills: string[];
  status: string;
  created_at: string;
  updated_at: string;
  match_score?: number | null;
}

export interface ResumeRecord {
  id: string;
  user_id: string | null;
  name: string;
  owner_email: string;
  content: string;
  storage_url: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CoverLetterRecord {
  id: string;
  user_id: string | null;
  job_id: string | null;
  resume_id: string | null;
  title: string;
  content: string;
  status: string;
  created_at: string;
  updated_at: string;
  job_title: string | null;
  company: string | null;
  resume_name: string | null;
}

export interface ApplicationRecord {
  id: string;
  user_id: string;
  job_id: string;
  resume_id: string | null;
  cover_letter_id: string | null;
  status: string;
  applied_at: string | null;
  external_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  job_title: string | null;
  company: string | null;
  resume_name: string | null;
}

export interface DashboardStats {
  jobs: number;
  resumes: number;
  cover_letters: number;
  applications: number;
  pulse: {
    jobs_analyzed_pct: number;
    resumes_optimized_pct: number;
    applications_submitted_pct: number;
  };
}

export interface MatchAnalysis {
  match_score: number;
  missing_skills: string[];
  ats_keyword_recommendations: string[];
  resume_improvement_suggestions: string[];
  interview_focus_areas: string[];
}

export interface KeywordDemand {
  keyword: string;
  demand_pct: number;
  postings: number;
}

export interface VisibilityResult {
  target_role: string;
  location: string | null;
  analyzed_postings: number;
  visibility_score: number;
  present_keywords: KeywordDemand[];
  missing_keywords: KeywordDemand[];
  recommendations: string[];
}
