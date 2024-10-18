
from crew import CustomerServiceCrew

def run_simulation():

    customer_service_crew = CustomerServiceCrew()
    crew = customer_service_crew.crew().kickoff()

    print(f"Crew process output: {crew}")

run_simulation()

    
