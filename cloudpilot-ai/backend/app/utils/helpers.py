import datetime
from typing import Dict, Any, List
from app.schemas.analyzer import AgentLog

# In-memory datastore
# Key: task_id, Value: AnalysisResult as dictionary
analysis_tasks: Dict[str, Any] = {}
infra_generations: Dict[str, Any] = {}

def add_agent_log(task_id: str, agent: str, message: str, status: str) -> AgentLog:
    """
    Appends a log to the task in the global store.
    """
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    log = AgentLog(agent=agent, message=message, timestamp=timestamp, status=status)
    
    if task_id in analysis_tasks:
        # Get existing logs
        logs = analysis_tasks[task_id].get("logs", [])
        
        # Check if there's an existing log for this agent in progress/pending, we update it
        updated = False
        for i, existing_log in enumerate(logs):
            if existing_log.get("agent") == agent and existing_log.get("status") in ["pending", "in_progress"]:
                logs[i] = log.model_dump()
                updated = True
                break
                
        if not updated:
            logs.append(log.model_dump())
            
        analysis_tasks[task_id]["logs"] = logs
        
    return log

def add_infra_agent_log(generation_id: str, agent: str, message: str, status: str) -> AgentLog:
    """
    Appends a log to the infrastructure task in the global store.
    """
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    log = AgentLog(agent=agent, message=message, timestamp=timestamp, status=status)
    
    if generation_id in infra_generations:
        logs = infra_generations[generation_id].get("logs", [])
        
        # Check if there's an existing log for this agent in progress/pending, we update it
        updated = False
        for i, existing_log in enumerate(logs):
            if existing_log.get("agent") == agent and existing_log.get("status") in ["pending", "in_progress"]:
                logs[i] = log.model_dump()
                updated = True
                break
                
        if not updated:
            logs.append(log.model_dump())
            
        infra_generations[generation_id]["logs"] = logs
        
    return log

