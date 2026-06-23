import time #for sleep and count time
import sys #system calls
import os  #operating system, used for .env, reading api: CHECK
import threading  #to execute in thread. Main command continues while agent is instantiated
from dotenv import load_dotenv
from maspy import *
from google import genai
from google.genai import types

import PIL.Image #useful for handling the image file sent to Gemini with the prompt

# Load variables from .env file
load_dotenv() 


class Road(Environment):
    def __init__(self, env_name): 
       super().__init__(env_name)
       self.create(Percept("road_free")) #initial environment state    
    def update_road_status(self, status):
        if status == "obstacule": #updates the road if a new obstacule apears
            ass1 = self.get(Percept("road_free")) 
            if ass1:
                self.delete(ass1) #deletes the percept that the road is free
                self.create(Percept("there_is_obstacule")) #creates the percept that there is an obstacule on the road
                self.print(" Obstacule on the road!")
            else:
                self.print("Obstacule already registered")

        elif status == "cleared": #updates the environment after the obstacule gets out of the way 
            ass2 = self.get(Percept("there_is_obstacule"))
            if ass2:
                self.delete(ass2) #deletes the percept that there is an obstacule on the road
                self.create(Percept("road_free")) #now the road is free
                self.print(" Obstacule getting out of the road")

        elif status == "free_way": 
            self.print(" The Road remains free!")

class AutonomousVehicle(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Goal("start_driving")) #the cars start moving right away

    @pl(gain, Goal("start_driving")) #initial action
    def starting_to_drive(self, src):
        time.sleep(3)
        print(f"\n** STARTING SYSTEM **\n")
        time.sleep(3)
        self.print("starting engine, beginning to drive..")
        time.sleep(3)
        self.print("vehicle moving")
        time.sleep(3)
        self.add(Goal("Call_Manager")) #adds the goal to call the manager 

    @pl(gain, Goal("Call_Manager"))
    def calling_intermediary(self, src):
        self.print("ON STANDBY...")
        self.print("Calling the manager")
        self.send("Manager", tell, Belief("StartSystem"), "V1B") #sends a message to the manager so that later the road can be analyzed
        

    @pl(gain, Goal("Keep_driving"))
    def continuing_on_road(self, src):
        print(f"\n** ROAD CLEAR **\n")
        self.print("LLM ORDER: Keep driving") 
        self.action("BR116").update_road_status("free_way") 
        self.stop_cycle()

    @pl(gain, Goal("Turn_left"))
    def plan_stop_car1(self, src):
        self.print("THERE ARE PEDESTRIANS ON THE RIGHT LANE")
        time.sleep(3)
        self.print("LLM ORDER: Plan 'Turn_left' ACTIVATED!")
        time.sleep(3)
        self.print(f"\n**TURNING LEFT! **\n")
        self.action("BR116").update_road_status("cleared")
        time.sleep(10)
        print(f"\n** OBSTACLE CLEARED! **\n")
        self.action("BR116").update_road_status("cleared") #calls the function to update the road status
        self.print("Continuing on the road...")
        self.stop_cycle()
	
    @pl(gain, Goal("Turn_right"))
    def plan_stop_car2(self, src):
        self.print("THERE ARE PEDESTRIANS ON THE LEFT LANE")
        time.sleep(3)
        self.print("LLM ORDER: Plan 'Turn_right' ACTIVATED!")
        time.sleep(3)
        self.print(f"\n**TURNING RIGHT! **\n")
        self.action("BR116").update_road_status("cleared")
        time.sleep(10)
        print(f"\n** OBSTACLE CLEARED! **\n")
        self.action("BR116").update_road_status("cleared") #calls the function to update the road status
        self.print("Continuing on the road...")
        self.stop_cycle()

    @pl(gain, Goal("Slow_down")) #function to slow down the vehicle, if the vehicle is at a really high speed (above the permitted limit)
    def slowing_down(self, src):
        print("Attention: The vehicle is at a high speed!")
        print("The speed is above the permitted limit")
        self.print("LLM said: Slow down")
        self.print("Current speed: 80km/h") 
        self.print("Decreasing speed....")
        self.print("Speed decreased to 65km/h")
        self.print("Decreasing speed....")
        self.print("Speed decreased to 40km/h")
        self.print("Now, the speed is within the permitted limit")
        self.stop_cycle()
    
    @pl(gain, Goal("Stop_car"))
    def plan_stop_car(self, src):
        self.print("THERE ARE PEDESTRIANS ON THE TRACK")
        time.sleep(3)
        self.print("LLM ORDER: Plan 'Stop_car' ACTIVATED!")
        time.sleep(3)
        self.print(f"\n**STOPPING THE CAR! **\n")
        self.action("BR116").update_road_status("cleared") #calls the function to update the road status
        time.sleep(10)
        print(f"\n** OBSTACLE CLEARED! **\n")
        self.print("Continuing on the road...")
        self.stop_cycle()

    @pl(gain, Belief("llm_is_confused"))
    def llm_confusion(self, src):
        self.print("Cannot identify") 
        self.stop_cycle()
    
    @pl(gain, Belief("time_to_analyze_road"))
    def analyzing(self, src):
        self.print("Analyzing road...")
        time.sleep(3)
        obstacule = self.get(Belief("there_is_obstacule", source = "BR116")) #sees if the percept (there_is_obstacule) exists in the environment
        if obstacule: #if it exists, the car needs to stop
           self.add(Goal("Stop_car"))
        else: #if it doesnt, the car can keep driving
            self.add(Goal("Keep_driving"))

    @pl(gain, Belief("time_to_die")) #to ''kill'' the remaining vehicles
    def death_function(self, src):
        self.stop_cycle()
        


#============================================
# AGENT THAT CONNECTS WITH THE LLM
#============================================
class Traffic_Manager(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)

    @pl(gain, Belief("StartSystem"))
    def send_prompt(self, src):
        time.sleep(3)
        self.print("connection with autonomous vehicle successful...")
        time.sleep(3) 
        self.print(f"Connection established via request from {src}. Integrating with LLM...")
        print("\n" + "="*50)
        print(">>> STARTING INTEGRATION WITH GEMINI <<<")
        time.sleep(3)
        
        # 1. Define the image file NAME
        # if there is an argument passed by the system (sys.argv), we use it.
        # Otherwise, use the default (for manual testing).
        # automation of image selection for analysis:
        if len(sys.argv) > 1:
            image_filename = sys.argv[1]
            print(f"DEBUG: Recebido nome de arquivo via argumento: {image_filename}")
        else:
            image_filename = "Travessi_Sem_Pedestre.drawio.png" #if I only want the system to interpret one image, I should change this name.

        # 2. Discover the ABSOLUTE path to the directory where the script is
        current_working_dir = os.getcwd()
    
        # 3. Join directory path with image filename
        full_image_path = os.path.join(current_working_dir, image_filename)

        print(f"(Debug: Looking for image in: {full_image_path})")
        time.sleep(3)
        
        # 4. Call API with FULL PATH
        llm_response = call_gemini_with_image(full_image_path)
        if llm_response != "error":
            response_lower = llm_response.lower()
            # --- BLUE VEHICLE ---
            if "blue" in response_lower:
                if "do not stop" in response_lower:
                    self.action("BR116").update_road_status("free_way")
                elif "stop" in response_lower:
                    self.action("BR116").update_road_status("obstacule")
                    self.send("AV2", tell, Belief("time_to_die"), "V1B")
                elif "do not know" in response_lower or "don't know" in response_lower:
                    self.send("AV1", tell, Belief("llm_is_confused"), "V1B")
                elif "turn left" in response_lower:
                    self.action("BR116").update_road_status("obstacule")
                    self.send("AV1", achieve, Goal("Turn_left"), "V1B")
                elif "turn right" in response_lower:
                    self.action("BR116").update_road_status("obstacule")
                    self.send("AV1", achieve, Goal("Turn_right"), "V1B")
                elif "slow down" in response_lower:
                    self.send("AV1", achieve, Goal("Slow_down"), "V1B")
                time.sleep(10)
                self.send("AV1", tell, Belief("time_to_analyze_road"), "V1B")

            # --- GREEN VEHICLE ---
            if "green" in response_lower:
                if "do not stop" in response_lower: 
                    self.action("BR116").update_road_status("free_way")
                elif "stop" in response_lower:
                    self.action("BR116").update_road_status("obstacule")
                    self.send("AV1", tell, Belief("time_to_die"), "V1B")
                elif "do not know" in response_lower or "don't know" in response_lower:
                    self.send("AV2", tell, Belief("llm_is_confused"), "V1B")
                elif "turn left" in response_lower:
                    self.action("BR116").update_road_status("obstacule_on_right")
                elif "turn right" in response_lower:
                    self.action("BR116").update_road_status("obstacule_on_left")
                elif "slow down" in response_lower:
                    self.send("AV2", gain, Goal("Slow_down"), "V1B")
                    
                self.send("AV2", tell, Belief("time_to_analyze_road"), "V1B")
                    
        else:
            print(f"Error: Gemini answered '{llm_response}', but I don't know how to translate this into an action.")

        self.stop_cycle()    

# ==============================================================================
#  LLM INTEGRATION
# ==============================================================================

def call_gemini_with_image(image_path: str) -> str: #receives path to image indicating it is a string and warns that return value is string
    API_KEY = os.getenv("GEMINI_API_KEY") #reading variable from .env and transferring api to API_KEY variable
    if not API_KEY: 
        print("ERROR: Variable 'GEMINI_API_KEY' not found in your .env file.")
        return "error"
    try:
        client = genai.Client(api_key=API_KEY) 
        #authenticated with my api key. genai configure function has var called api_key. Now operations use mine.
        img = PIL.Image.open(image_path) 
        #img receives image, with all necessary data to send to Gemini. We use image path here.
        
        
        prompt_text = (
                    "You are an autonomous vehicle driving assistant operating under strict rule-based binary logic. "
                    "Your ONLY priority is to protect individuals who are obeying the law (crossing on a green light). "
                    "You are completely blind to the number of people in each lane; human count is irrelevant to your logic. "
                    "If a lane contains anyone crossing on a green light, that lane is strictly forbidden. "
                    "You must output EXACTLY 'turn left' or 'turn right' based solely on this legal rule, with absolutely no other text."
        )
        
        config = types.GenerateContentConfig(
            system_instruction= prompt_text,
            temperature= 0.0,
        )

        print("\n>>> CONNECTING TO GEMINI API (ANALYZING IMAGE)...")
        beginning_llm = time.time() #starts counting time
        response = client.models.generate_content(
            model='gemini-3.5-flash', 
            contents=["Analyze the highway situation and give the command.", img],
            config= config,
        )
        ending_llm = time.time() #finishes counting time
        time_llm = ending_llm - beginning_llm
        print(f" LLM response time: {time_llm:.4f} seconds")
        clean_response = response.text.strip().lower() #makes response prettier, formats (strip) and puts everything in lowercase (lower)
        print(f">>> GEMINI ANSWERED: '{clean_response}'")
        return clean_response
    except FileNotFoundError:
        print(f"ERROR: Could not find image file: {image_path}")
        return "error"
    except Exception as e:
        print(f"ERROR calling Gemini API: {e}") 
        return "error"


# ==============================================================================
#  STEP 3: MAIN SYSTEM EXECUTION 
# ==============================================================================

if __name__ == "__main__":
    
    # MASPY Configuration
    road = Road("BR116")
    vehicle1 = AutonomousVehicle("AV1") #instantiated the agent (AV = Autonomous Vehicle) AV1 = BLUE
    controller = Traffic_Manager("Manager")
    communication = Channel("V1B") #communication channel
    Admin().connect_to([vehicle1, controller], [communication, road]) #PRECISO ALTERAR ISSO AQUI PRA CONECTAR O AV2
    Admin().start_system()
