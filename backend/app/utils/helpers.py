import datetime
from typing import Dict, Any, List
from app.schemas.analyzer import AgentLog

from app.utils.database import SqliteDict

# SQLite-backed persistent datastores
analysis_tasks = SqliteDict("analyses", "task_id")
infra_generations = SqliteDict("generations", "generation_id")
deployments = SqliteDict("deployments", "deployment_id")

def add_deployment_log(deployment_id: str, stage: str, message: str, status: str) -> Dict[str, Any]:
    """
    Appends a log to the active deployment in the global store.
    """
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    log = {"stage": stage, "message": message, "timestamp": timestamp, "status": status}
    
    if deployment_id in deployments:
        dep_data = deployments[deployment_id]
        logs = dep_data.get("logs", [])
        
        updated = False
        for i, existing_log in enumerate(logs):
            if existing_log.get("stage") == stage and existing_log.get("status") in ["pending", "in_progress"]:
                logs[i] = log
                updated = True
                break
                
        if not updated:
            logs.append(log)
            
        dep_data["logs"] = logs
        
        # Append to console list
        console = dep_data.get("console", [])
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.append(f"[{time_str}] [{stage}] {message}")
        dep_data["console"] = console
        
        deployments[deployment_id] = dep_data
        
    return log

def add_agent_log(task_id: str, agent: str, message: str, status: str) -> AgentLog:
    """
    Appends a log to the task in the global store.
    """
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    log = AgentLog(agent=agent, message=message, timestamp=timestamp, status=status)
    
    if task_id in analysis_tasks:
        task_data = analysis_tasks[task_id]
        # Get existing logs
        logs = task_data.get("logs", [])
        
        # Check if there's an existing log for this agent in progress/pending, we update it
        updated = False
        for i, existing_log in enumerate(logs):
            if existing_log.get("agent") == agent and existing_log.get("status") in ["pending", "in_progress"]:
                logs[i] = log.model_dump()
                updated = True
                break
                
        if not updated:
            logs.append(log.model_dump())
            
        task_data["logs"] = logs
        analysis_tasks[task_id] = task_data
        
    return log

def add_infra_agent_log(generation_id: str, agent: str, message: str, status: str) -> AgentLog:
    """
    Appends a log to the infrastructure task in the global store.
    """
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    log = AgentLog(agent=agent, message=message, timestamp=timestamp, status=status)
    
    if generation_id in infra_generations:
        gen_data = infra_generations[generation_id]
        logs = gen_data.get("logs", [])
        
        # Check if there's an existing log for this agent in progress/pending, we update it
        updated = False
        for i, existing_log in enumerate(logs):
            if existing_log.get("agent") == agent and existing_log.get("status") in ["pending", "in_progress"]:
                logs[i] = log.model_dump()
                updated = True
                break
                
        if not updated:
            logs.append(log.model_dump())
            
        gen_data["logs"] = logs
        infra_generations[generation_id] = gen_data
        
    return log

