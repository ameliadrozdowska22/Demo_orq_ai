from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import openai
from openai import OpenAI
from langchain_openai import ChatOpenAI

openai.api_key = "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"

client = OpenAI(
    api_key = openai.api_key,
)
GPT_MODEL = "gpt-4o-mini"

# manager_llm
manager_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, openai_api_key="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")

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
            verbose=True
        )
    
    @agent
    def technical_support_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['technical_support_agent'],
            allow_delegation=False,
            verbose=True
        )
    
    @agent
    def marketing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['marketing_agent'],
            allow_delegation=False,
            verbose=True
        )
    
    @agent
    def human_resource_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['human_resource_agent'],
            allow_delegation=False,
            verbose=True
        )
    
    # manager_agent
    manager = Agent(
            role ="Project Manager",
            goal=" Efficiently manage the crew and ensure high-quality task completion",
            backstory=" You're an experienced project manager, skilled in overseeing complex projects and guiding teams to success. Your role is to coordinate the efforts of the crew members, ensuring that each task is completed on time and to the highest standard.",
            allow_delegation=True,
            verbose=True
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
            process=Process.hierarchical,
            # manager_agent=self.manager,
            manager_llm = manager_llm,
            verbose=True, 
        )
    
    