export interface LanguageInfo {
  name: string;
  percentage: number;
}

export interface RepoMetadata {
  languages: LanguageInfo[];
  frameworks: string[];
  frontend: string[];
  backend: string[];
  databases: string[];
  package_managers: string[];
  docker_readiness: boolean;
  docker_compose: boolean;
  env_variables: string[];
  ci_cd: string[];
  terraform: boolean;
  infrastructure_files: string[];
  readme_quality: 'High' | 'Medium' | 'Low';
  license: string;
  build_commands: string[];
  run_commands: string[];
  test_frameworks: string[];
}

export interface CostBreakdown {
  compute: number;
  database: number;
  storage: number;
  data_transfer: number;
  [key: string]: number;
}

export interface DeploymentRecommendation {
  target: 'AWS App Runner' | 'AWS ECS' | 'AWS Lambda' | 'AWS Amplify';
  why: string;
  estimated_monthly_cost: number;
  cost_breakdown: CostBreakdown;
  confidence_score: number;
}

export interface HealthBreakdown {
  documentation: number;
  docker: number;
  security: number;
  environment: number;
  deployment: number;
  organization: number;
}

export interface ChecklistItem {
  label: string;
  status: 'checked' | 'warning' | 'error';
}

export interface AgentLog {
  agent: string;
  message: string;
  timestamp: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export interface AnalysisResult {
  repository_url: string;
  repository_name: string;
  repository_owner: string;
  analysis_time: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  metadata: RepoMetadata;
  recommendation: DeploymentRecommendation;
  health_score: number;
  health_breakdown: HealthBreakdown;
  checklist: ChecklistItem[];
  ai_summary: string;
  logs: AgentLog[];
  error?: string;
}

export interface AnalyzeRequest {
  repository_url: string;
}

export interface AnalyzeResponse {
  task_id: string;
  status: string;
}

// ==========================================
// AI Infrastructure Generator Types
// ==========================================

export interface InfrastructureRequest {
  repository_url: string;
}

export interface InfrastructureResponse {
  generation_id: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  progress: number;
  detected_framework: string;
  generated_files: { [path: string]: string };
  validation_score: number;
  next_step: string;
  error?: string;
}
