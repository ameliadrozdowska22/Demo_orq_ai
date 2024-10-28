from typing import List
from crewai.flow.flow import Flow, listen, start,or_, router
from pydantic import BaseModel
from crew import CustomerServiceCrew, EvaluationCrew
import json

# State model to track customer queries and evaluations
class TaskState(BaseModel):
    approved: bool = False
    last_feedback:str = ""
    current_output: str = "" 

class CustomerQueryFlow(Flow[TaskState]):
    initial_state = TaskState

    @start()
    def start_flow(self):
        print("Starting Task")
    
    @listen(or_(start_flow,"improve_based_on_feedback"))
    async def handle_task(self):
        self.state.current_output = str( await CustomerServiceCrew().crew().kickoff_async(inputs={"feedback":self.state.last_feedback,"last_answer":self.state.current_output}))

    @router(handle_task)
    async def evaluate_task(self):
        if len(str(self.state.current_output)) > 0:
            
            evaluation = await EvaluationCrew().crew().kickoff_async(inputs={"last_answer":self.state.current_output})
            evaluation = evaluation.json_dict

            # Accessing approved and feedback keys from the evaluation
            self.state.approved = evaluation.get("approved", False)
            self.state.last_feedback = evaluation.get("feedback", "")

            print("Evaluation Completed")
        else:
            print("No customer queries to evaluate.")

        if self.state.approved:
            exit()
        else:
            return "improve_based_on_feedback"


        print("Task Completed")
