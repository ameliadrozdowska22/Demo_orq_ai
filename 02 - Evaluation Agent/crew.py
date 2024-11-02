from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai import LLM
import openai
from openai import OpenAI

from pydantic import BaseModel
from typing import Optional

import os
openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key = openai.api_key,
)
GPT_MODEL = LLM(model="gpt-4o-mini", temperature=0.7)

class EvaluationOutput(BaseModel):
    approved: Optional[bool]
    feedback: Optional[str]

@CrewBase
class EvaluationCrew:

    agents_config = 'config/eval_agents.yaml'
    tasks_config = 'config/eval_tasks.yaml'

    @agent
    def evaluation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['evaluation_agent'],
            verbose=True,
            allow_delegation=False,
            llm=GPT_MODEL
        )
    
    @task
    def customer_query(self) -> Task:
        return Task(
            config=self.tasks_config['evaluate_customer_interaction'],
            output_json=EvaluationOutput
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
    

@CrewBase
class CustomerServiceCrew:
    """Customer Service crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def accounting_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['accounting_agent'],
            allow_delegation=False,
            verbose=True,
            llm=GPT_MODEL
        )
    
    @agent
    def technical_support_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['technical_support_agent'],
            allow_delegation=False,
            verbose=True,
            llm=GPT_MODEL
        )
    
    @agent
    def marketing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['marketing_agent'],
            allow_delegation=False,
            verbose=True,
            llm=GPT_MODEL
        )
    
    @agent
    def human_resource_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['human_resource_agent'],
            allow_delegation=False,
            verbose=True,
            llm=GPT_MODEL
        )
    
    # manager_agent
    manager = Agent(
            role ="Project Manager",
            goal=" Efficiently manage the crew and ensure high-quality task completion",
            backstory=" You're an experienced project manager, skilled in overseeing complex projects and guiding teams to success. Your role is to coordinate the efforts of the crew members, ensuring that each task is completed on time and to the highest standard.",
            allow_delegation=True,
            verbose=True,\
            llm=GPT_MODEL
        )
    
    @task
    def customer_query(self) -> Task:
        return Task(
            config=self.tasks_config['customer_query'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CustomerServiceCrew"""
        return Crew(
            agents=self.agents,  
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True, 
        )