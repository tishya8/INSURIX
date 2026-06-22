from app.services.planner_service import generate_plan
import re
from fastapi import FastAPI
from app.services.claim_service import (
    get_user_policies,
    create_claim,
    get_claim_status,
    update_claim_status
)
from app.services.rag_service import ask_policy

from app.services.policy_service import (
    get_user_policies,
    get_policy_document
)

from app.services.intent_service import detect_intent

from fastapi.middleware.cors import CORSMiddleware

from app.services.session_service import conversation_state

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "INSURIX API Running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/users/{user_id}/policies")
def fetch_user_policies(user_id: int):

    policies = get_user_policies(user_id)

    return policies

@app.post("/claims")
def create_new_claim(
    policy_id: int,
    incident_type: str,
    description: str
):

    claim_id = create_claim(
        policy_id,
        incident_type,
        description
    )

    return {
        "claim_id": claim_id,
        "status": "SUBMITTED"
    }

@app.get("/claims/{claim_id}")
def fetch_claim_status(claim_id: int):

    claim = get_claim_status(claim_id)

    return claim

@app.put("/claims/{claim_id}/status")
def update_status(
    claim_id: int,
    status: str
):

    update_claim_status(
        claim_id,
        status
    )

    return {
        "message": "Claim status updated",
        "claim_id": claim_id,
        "status": status
    }


@app.get("/policies/{policy_id}/document")
def get_document(policy_id: int):

    document = get_policy_document(policy_id)

    if document is None:
        return {
            "message": "Policy document not found"
        }

    return document


def normalize_query(query):
    return query.strip().rstrip("?!.")

# @app.post("/ask-policy")
# def ask_policy_api(request: dict):

#     policy_id = request["policy_id"]
#     question = request["question"]

#     session_id = request.get(
#         "session_id",
#         "default_user"
#     )

#     # ---------------------------------------------------
#     # Pending Claim Workflow
#     # ---------------------------------------------------

#     if session_id in conversation_state:

#         pending = conversation_state[
#             session_id
#         ]

#         if pending["action"] == "CREATE_CLAIM":

#             claim_id = create_claim(

#                 policy_id,

#                 pending["incident_type"],

#                 question
#             )

#             del conversation_state[
#                 session_id
#             ]

#             return {
#                 "answer":
#                 f"""
# Claim created successfully.

# Claim ID: {claim_id}
# Status: SUBMITTED
# Incident Type: {pending['incident_type']}
# Description: {question}
# """
#             }

#     # ---------------------------------------------------
#     # Create Execution Plan
#     # ---------------------------------------------------

#     plan = create_plan(question)

#     print("\nPLAN:")
#     print(plan)

#     # ---------------------------------------------------
#     # Multi-Step Execution
#     # ---------------------------------------------------

#     if len(plan) > 1:

#         responses = []

#         for task in plan:

#             task_intent = task["intent"]
#             task_query = task["query"]

#             # -----------------------------
#             # POLICY QUERY
#             # -----------------------------

#             if task_intent == "POLICY_QUERY":

#                 answer = ask_policy(
#                     policy_id,
#                     normalize_query(task_query)
#                 )

#                 responses.append(
#                     f"""
# Question:
# {task_query}

# Answer:
# {answer}
# """
#                 )

#             # -----------------------------
#             # TRACK CLAIM
#             # -----------------------------

#             elif task_intent == "TRACK_CLAIM":

#                 import re

#                 match = re.search(
#                     r"\d+",
#                     task_query
#                 )

#                 if match:

#                     claim_id = int(
#                         match.group()
#                     )

#                     claim = get_claim_status(
#                         claim_id
#                     )

#                     if claim:

#                         responses.append(
#                             f"""
# Claim Details

# Claim ID: {claim['claim_id']}
# Status: {claim['claim_status']}
# Incident: {claim['incident_type']}
# Description: {claim['description']}
# """
#                         )

#                     else:

#                         responses.append(
#                             f"No claim found with Claim ID {claim_id}."
#                         )

#                 else:

#                     responses.append(
#                         "Please provide a valid claim ID."
#                     )

#         return {
#             "answer":
#             "\n\n".join(responses)
#         }

#     # ---------------------------------------------------
#     # Single Task Handling
#     # ---------------------------------------------------

#     intent = plan[0]["intent"]

#     # -----------------------------
#     # POLICY QUERY
#     # -----------------------------

#     if intent == "POLICY_QUERY":

#         answer = ask_policy(
#             policy_id,
#             normalize_query(plan[0]["query"])
#         )

#         return {
#             "answer": answer
#         }

#     # -----------------------------
#     # CREATE CLAIM
#     # -----------------------------

#     elif intent == "CREATE_CLAIM":

#         incident_type = "GENERAL"

#         if "theft" in question.lower():

#             incident_type = "THEFT"

#         elif "accident" in question.lower():

#             incident_type = "ACCIDENT"

#         elif "flood" in question.lower():

#             incident_type = "FLOOD"

#         conversation_state[
#             session_id
#         ] = {

#             "action":
#             "CREATE_CLAIM",

#             "incident_type":
#             incident_type
#         }

#         return {

#             "answer":
#             f"""
# Claim creation started.

# Incident Type:
# {incident_type}

# Please provide a brief description of the incident.
# """
#         }

#     # -----------------------------
#     # TRACK CLAIM
#     # -----------------------------

#     elif intent == "TRACK_CLAIM":

#         import re

#         match = re.search(
#             r"\d+",
#             question
#         )

#         if match:

#             claim_id = int(
#                 match.group()
#             )

#             claim = get_claim_status(
#                 claim_id
#             )

#             if claim:

#                 return {
#                     "answer":
#                     f"""
# Claim Details

# Claim ID: {claim['claim_id']}
# Status: {claim['claim_status']}
# Incident: {claim['incident_type']}
# Description: {claim['description']}
# """
#                 }

#             return {
#                 "answer":
#                 f"No claim found with Claim ID {claim_id}."
#             }

#         return {
#             "answer":
#             "Please provide a valid claim ID."
#         }

#     # -----------------------------
#     # UNKNOWN
#     # -----------------------------

#     return {

#         "answer":
#         """
# I could not understand your request.

# You can:
# • Ask policy-related questions
# • Create a claim
# • Track a claim status
# """
#     }


# @app.post("/ask-policy")
# def ask_policy_api(request: dict):

#     policy_id = request["policy_id"]
#     question = request["question"]

#     session_id = request.get(
#         "session_id",
#         "default_user"
#     )


#     # ---------------------------------------------------
#     # Pending Claim Workflow
#     # ---------------------------------------------------

#     if session_id in conversation_state:

#         pending = conversation_state[session_id]


#         # ===============================================
#         # STEP 1 : WAITING FOR INCIDENT TYPE
#         # ===============================================

#         if (
#             pending["action"] == "CREATE_CLAIM"
#             and pending["step"] == "WAITING_FOR_INCIDENT_TYPE"
#         ):

#             incident = question.lower()


#             incident_type = None


#             if "theft" in incident:
#                 incident_type = "THEFT"

#             elif "accident" in incident:
#                 incident_type = "ACCIDENT"

#             elif "flood" in incident:
#                 incident_type = "FLOOD"

#             elif "fire" in incident:
#                 incident_type = "FIRE"

#             elif "other" in incident:
#                 incident_type = "OTHER"


#             if incident_type:


#                 conversation_state[session_id] = {

#                     "action":
#                     "CREATE_CLAIM",

#                     "step":
#                     "WAITING_FOR_DESCRIPTION",

#                     "incident_type":
#                     incident_type
#                 }


#                 return {

#                     "answer":
#                     """
# Please provide a brief description of the incident.
# """
#                 }


#             return {

#                 "answer":
#                 """
# Please select a valid incident type:

# 1. Theft
# 2. Accident
# 3. Flood
# 4. Fire
# 5. Other

# Reply with incident type.
# """
#             }



#         # ===============================================
#         # STEP 2 : WAITING FOR DESCRIPTION
#         # ===============================================

#         if (
#             pending["action"] == "CREATE_CLAIM"
#             and pending["step"] == "WAITING_FOR_DESCRIPTION"
#         ):


#             conversation_state[session_id] = {


#                 "action":
#                 "CREATE_CLAIM",


#                 "step":
#                 "WAITING_FOR_CONFIRMATION",


#                 "incident_type":
#                 pending["incident_type"],


#                 "description":
#                 question
#             }


#             return {


#                 "answer":
#                 f"""
# Please confirm:

# Incident Type:
# {pending['incident_type']}

# Description:
# {question}


# Reply YES to create the claim.
# """
#             }



#         # ===============================================
#         # STEP 3 : WAITING FOR CONFIRMATION
#         # ===============================================

#         if (
#             pending["action"] == "CREATE_CLAIM"
#             and pending["step"] == "WAITING_FOR_CONFIRMATION"
#         ):


#             if question.lower() == "yes":


#                 claim_id = create_claim(

#                     policy_id,

#                     pending["incident_type"],

#                     pending["description"]

#                 )


#                 del conversation_state[session_id]


#                 return {


#                     "answer":
#                     f"""
# Claim created successfully.

# Claim ID:
# {claim_id}

# Status:
# SUBMITTED

# Incident Type:
# {pending['incident_type']}

# Description:
# {pending['description']}
# """
#                 }


#             return {


#                 "answer":
#                 """
# Claim creation cancelled.

# You can start again by saying:
# create a claim
# """
#             }



#     # ---------------------------------------------------
#     # Create Execution Plan
#     # ---------------------------------------------------

#     plan = create_plan(question)


#     print("\nPLAN:")
#     print(plan)



#     # ---------------------------------------------------
#     # Multi-Step Execution
#     # ---------------------------------------------------

#     if len(plan) > 1:


#         responses = []


#         for task in plan:


#             task_intent = task["intent"]

#             task_query = task["query"]



#             if task_intent == "POLICY_QUERY":


#                 answer = ask_policy(

#                     policy_id,

#                     normalize_query(task_query)

#                 )


#                 responses.append(

#                     f"""
# Question:
# {task_query}

# Answer:
# {answer}
# """
#                 )



#             elif task_intent == "TRACK_CLAIM":


#                 import re


#                 match = re.search(
#                     r"\d+",
#                     task_query
#                 )


#                 if match:


#                     claim_id = int(match.group())


#                     claim = get_claim_status(
#                         claim_id
#                     )


#                     if claim:


#                         responses.append(

#                             f"""
# Claim Details

# Claim ID:
# {claim['claim_id']}

# Status:
# {claim['claim_status']}

# Incident:
# {claim['incident_type']}

# Description:
# {claim['description']}
# """
#                         )


#                     else:


#                         responses.append(

#                             f"No claim found with Claim ID {claim_id}."

#                         )


#                 else:


#                     responses.append(

#                         "Please provide a valid claim ID."

#                     )



#         return {


#             "answer":

#             "\n\n".join(responses)

#         }





#     # ---------------------------------------------------
#     # Single Task Handling
#     # ---------------------------------------------------

#     intent = plan[0]["intent"]




#     # POLICY QUERY

#     if intent == "POLICY_QUERY":


#         answer = ask_policy(

#             policy_id,

#             normalize_query(plan[0]["query"])

#         )


#         return {


#             "answer":
#             answer

#         }





#     # ===================================================
#     # CREATE CLAIM NEW WORKFLOW
#     # ===================================================


#     elif intent == "CREATE_CLAIM":


#         incident_type = None



#         if "theft" in question.lower():

#             incident_type = "THEFT"


#         elif "accident" in question.lower():

#             incident_type = "ACCIDENT"



#         elif "flood" in question.lower():

#             incident_type = "FLOOD"



#         elif "fire" in question.lower():

#             incident_type = "FIRE"




#         # User already gave incident type

#         if incident_type:


#             conversation_state[session_id] = {


#                 "action":

#                 "CREATE_CLAIM",


#                 "step":

#                 "WAITING_FOR_DESCRIPTION",


#                 "incident_type":

#                 incident_type

#             }


#             return {


#                 "answer":
#                 """
# Please provide a brief description of the incident.
# """
#             }



#         # User only said create claim


#         conversation_state[session_id] = {


#             "action":

#             "CREATE_CLAIM",


#             "step":

#             "WAITING_FOR_INCIDENT_TYPE"

#         }



#         return {


#             "answer":
#             """
# Please select the incident type:

# 1. Theft
# 2. Accident
# 3. Flood
# 4. Fire
# 5. Other

# Reply with incident type.
# """
#         }






#     # TRACK CLAIM

#     elif intent == "TRACK_CLAIM":


#         import re


#         match = re.search(
#             r"\d+",
#             question
#         )


#         if match:


#             claim_id = int(match.group())


#             claim = get_claim_status(

#                 claim_id

#             )


#             if claim:


#                 return {


#                     "answer":
#                     f"""
# Claim Details

# Claim ID:
# {claim['claim_id']}

# Status:
# {claim['claim_status']}

# Incident:
# {claim['incident_type']}

# Description:
# {claim['description']}
# """
#                 }



#             return {


#                 "answer":
#                 f"No claim found with Claim ID {claim_id}."

#             }


#         return {


#             "answer":
#             "Please provide a valid claim ID."

#         }





#     return {


#         "answer":
#         """
# I could not understand your request.

# You can:

# • Ask policy-related questions
# • Create a claim
# • Track a claim status

# """
#     }


# @app.post("/ask-policy")
# def ask_policy_api(request: dict):

#     policy_id = request["policy_id"]
#     question = request["question"]

#     session_id = request.get(
#         "session_id",
#         "default_user"
#     )


#     # ===================================================
#     # Helper Function - Detect Incident Type
#     # ===================================================

#     def detect_incident_type(text):

#         text = text.lower()


#         if any(word in text for word in [
#             "theft",
#             "threft",
#             "stolen",
#             "steal",
#             "robbery"
#         ]):

#             return "THEFT"



#         elif any(word in text for word in [
#             "accident",
#             "crash",
#             "crashed",
#             "collision",
#             "hit"
#         ]):

#             return "ACCIDENT"



#         elif any(word in text for word in [
#             "flood",
#             "water damage",
#             "rain"
#         ]):

#             return "FLOOD"



#         elif any(word in text for word in [
#             "fire",
#             "burn",
#             "flame"
#         ]):

#             return "FIRE"



#         elif "other" in text:

#             return "OTHER"



#         return None





#     # ===================================================
#     # Pending Claim Workflow
#     # ===================================================


#     if session_id in conversation_state:


#         pending = conversation_state[session_id]



#         # -----------------------------------------------
#         # WAITING FOR INCIDENT TYPE
#         # -----------------------------------------------


#         if (
#             pending["action"] == "CREATE_CLAIM"
#             and
#             pending["step"] == "WAITING_FOR_INCIDENT_TYPE"
#         ):


#             incident_type = detect_incident_type(question)



#             if incident_type:


#                 conversation_state[session_id] = {


#                     "action":
#                     "CREATE_CLAIM",


#                     "step":
#                     "WAITING_FOR_DESCRIPTION",


#                     "incident_type":
#                     incident_type

#                 }



#                 return {


#                     "answer":
#                     """
# Please provide a brief description of the incident.
# """
#                 }




#             return {


#                 "answer":
#                 """
# Please select a valid incident type:

# 1. Theft
# 2. Accident
# 3. Flood
# 4. Fire
# 5. Other

# Reply with incident type.
# """
#             }






#         # -----------------------------------------------
#         # WAITING FOR DESCRIPTION
#         # -----------------------------------------------


#         if (
#             pending["action"] == "CREATE_CLAIM"
#             and
#             pending["step"] == "WAITING_FOR_DESCRIPTION"
#         ):



#             conversation_state[session_id] = {


#                 "action":
#                 "CREATE_CLAIM",


#                 "step":
#                 "WAITING_FOR_CONFIRMATION",


#                 "incident_type":
#                 pending["incident_type"],


#                 "description":
#                 question

#             }




#             return {


#                 "answer":
#                 f"""
# Please confirm:

# Incident Type:
# {pending['incident_type']}


# Description:
# {question}


# Reply YES to create the claim.
# """
#             }






#         # -----------------------------------------------
#         # WAITING FOR CONFIRMATION
#         # -----------------------------------------------


#         if (
#             pending["action"] == "CREATE_CLAIM"
#             and
#             pending["step"] == "WAITING_FOR_CONFIRMATION"
#         ):



#             if question.lower() in [
#                 "yes",
#                 "y",
#                 "confirm"
#             ]:



#                 claim_id = create_claim(

#                     policy_id,

#                     pending["incident_type"],

#                     pending["description"]

#                 )



#                 del conversation_state[session_id]



#                 return {


#                     "answer":
#                     f"""
# Claim created successfully.

# Claim ID:
# {claim_id}


# Status:
# SUBMITTED


# Incident Type:
# {pending['incident_type']}


# Description:
# {pending['description']}
# """
#                 }




#             else:



#                 del conversation_state[session_id]



#                 return {


#                     "answer":
#                     """
# Claim creation cancelled.

# You can start again by saying:
# create a claim
# """
#                 }







#     # ===================================================
#     # Create Execution Plan
#     # ===================================================


#     plan = create_plan(question)



#     print("\nPLAN:")
#     print(plan)





#     # ===================================================
#     # Multi Step Execution
#     # ===================================================


#     if len(plan) > 1:


#         responses = []



#         for task in plan:


#             task_intent = task["intent"]

#             task_query = task["query"]




#             if task_intent == "POLICY_QUERY":


#                 answer = ask_policy(

#                     policy_id,

#                     normalize_query(task_query)

#                 )



#                 responses.append(answer)





#             elif task_intent == "TRACK_CLAIM":


#                 import re



#                 match = re.search(

#                     r"\d+",

#                     task_query

#                 )



#                 if match:


#                     claim_id = int(match.group())



#                     claim = get_claim_status(

#                         claim_id

#                     )



#                     if claim:


#                         responses.append(

#                             f"""
# Claim ID:
# {claim['claim_id']}

# Status:
# {claim['claim_status']}

# Incident:
# {claim['incident_type']}

# Description:
# {claim['description']}
# """
#                         )



#                     else:


#                         responses.append(

#                             f"No claim found with ID {claim_id}"

#                         )



#         return {


#             "answer":

#             "\n\n".join(responses)

#         }







#     # ===================================================
#     # Single Task
#     # ===================================================


#     intent = plan[0]["intent"]






#     # ---------------------------------------------------
#     # POLICY QUERY
#     # ---------------------------------------------------


#     if intent == "POLICY_QUERY":


#         answer = ask_policy(

#             policy_id,

#             normalize_query(plan[0]["query"])

#         )



#         return {


#             "answer":
#             answer

#         }







#     # ---------------------------------------------------
#     # CREATE CLAIM
#     # ---------------------------------------------------


#     elif intent == "CREATE_CLAIM":




#         incident_type = detect_incident_type(question)





#         # User already mentioned incident type

#         if incident_type:



#             conversation_state[session_id] = {


#                 "action":
#                 "CREATE_CLAIM",


#                 "step":
#                 "WAITING_FOR_DESCRIPTION",


#                 "incident_type":
#                 incident_type

#             }




#             return {


#                 "answer":
#                 """
# Please provide a brief description of the incident.
# """
#             }







#         # User only said create claim


#         conversation_state[session_id] = {


#             "action":
#             "CREATE_CLAIM",


#             "step":
#             "WAITING_FOR_INCIDENT_TYPE"

#         }




#         return {


#             "answer":
#             """
# Please select the incident type:

# 1. Theft
# 2. Accident
# 3. Flood
# 4. Fire
# 5. Other

# Reply with incident type.
# """
#         }








#     # ---------------------------------------------------
#     # TRACK CLAIM
#     # ---------------------------------------------------


#     elif intent == "TRACK_CLAIM":


#         import re



#         match = re.search(

#             r"\d+",

#             question

#         )



#         if match:


#             claim_id = int(match.group())



#             claim = get_claim_status(

#                 claim_id

#             )



#             if claim:


#                 return {


#                     "answer":
#                     f"""
# Claim Details

# Claim ID:
# {claim['claim_id']}

# Status:
# {claim['claim_status']}

# Incident:
# {claim['incident_type']}

# Description:
# {claim['description']}
# """
#                 }





#             return {


#                 "answer":
#                 f"No claim found with Claim ID {claim_id}"

#             }





#         return {


#             "answer":
#             "Please provide a valid claim ID."

#         }







#     # ---------------------------------------------------
#     # UNKNOWN
#     # ---------------------------------------------------


#     return {


#         "answer":
#         """
# I could not understand your request.

# You can:

# • Ask policy questions
# • Create a claim
# • Track claim status
# """
#     }


@app.post("/ask-policy")
def ask_policy_api(request: dict):

    policy_id = request["policy_id"]
    question = request["question"]

    session_id = request.get(
        "session_id",
        "default_user"
    )


    # ===================================================
    # Detect Incident Type
    # ===================================================

    def detect_incident_type(text):

        text = text.lower()


        if any(word in text for word in [
            "theft",
            "threft",
            "stolen",
            "steal",
            "robbery"
        ]):

            return "THEFT"



        elif any(word in text for word in [
            "accident",
            "crash",
            "crashed",
            "collision",
            "hit"
        ]):

            return "ACCIDENT"



        elif any(word in text for word in [
            "flood",
            "water damage",
            "rain"
        ]):

            return "FLOOD"



        elif any(word in text for word in [
            "fire",
            "burn",
            "flame"
        ]):

            return "FIRE"



        elif "other" in text:

            return "OTHER"


        return None





    # ===================================================
    # Pending Claim Workflow
    # ===================================================


    if session_id in conversation_state:


        pending = conversation_state[session_id]



        # -----------------------------------------------
        # WAITING INCIDENT TYPE
        # -----------------------------------------------


        if (
            pending["action"] == "CREATE_CLAIM"
            and
            pending["step"] == "WAITING_FOR_INCIDENT_TYPE"
        ):


            incident_type = detect_incident_type(question)



            if incident_type:


                conversation_state[session_id] = {


                    "action":
                    "CREATE_CLAIM",


                    "step":
                    "WAITING_FOR_DESCRIPTION",


                    "incident_type":
                    incident_type

                }


                return {


                    "answer":
                    """
Please provide a brief description of the incident.
"""
                }





            return {


                "answer":
                """
Please select a valid incident type:

1. Theft
2. Accident
3. Flood
4. Fire
5. Other

Reply with incident type.
"""
            }





        # -----------------------------------------------
        # WAITING DESCRIPTION
        # -----------------------------------------------


        if (
            pending["action"] == "CREATE_CLAIM"
            and
            pending["step"] == "WAITING_FOR_DESCRIPTION"
        ):



            conversation_state[session_id] = {


                "action":
                "CREATE_CLAIM",


                "step":
                "WAITING_FOR_CONFIRMATION",


                "incident_type":
                pending["incident_type"],


                "description":
                question

            }



            return {


                "answer":
                f"""
Please confirm:

Incident Type:
{pending['incident_type']}


Description:
{question}


Reply YES to create the claim.
"""
            }





        # -----------------------------------------------
        # WAITING CONFIRMATION
        # -----------------------------------------------


        if (
            pending["action"] == "CREATE_CLAIM"
            and
            pending["step"] == "WAITING_FOR_CONFIRMATION"
        ):



            if question.lower() in [
                "yes",
                "y",
                "confirm"
            ]:



                claim_id = create_claim(

                    policy_id,

                    pending["incident_type"],

                    pending["description"]

                )



                del conversation_state[session_id]



                return {


                    "answer":
                    f"""
Claim created successfully.

Claim ID:
{claim_id}


Status:
SUBMITTED


Incident Type:
{pending['incident_type']}


Description:
{pending['description']}
"""
                }





            elif question.lower() in [
                "no",
                "n",
                "cancel"
            ]:



                del conversation_state[session_id]


                return {


                    "answer":
                    """
Claim creation cancelled.

You can start again by saying:
create a claim
"""
                }





            else:


                return {


                    "answer":
                    """
I did not understand.

Please reply YES to create the claim
or NO to cancel.
"""
                }







    # ===================================================
    # Create Plan
    # ===================================================


    plan = generate_plan(question)


    print("\nPLAN:")
    print(plan)

    if not plan:

        return {
            "answer":
            """
    I could not understand your request.

    Currently I can help with:

    • Policy coverage questions
    • Claim creation
    • Claim status tracking

    Examples:

    • Is theft covered?
    • Create a theft claim
    • Track claim 7

    Please try asking in one of the above formats.
    """
        }



    # ===================================================
    # MULTI INTENT EXECUTION
    # ===================================================


    if len(plan) > 1:


        responses = []



        for task in plan:


            task_intent = task["intent"]

            task_query = task["query"]




            # -------------------------------------------
            # POLICY QUERY
            # -------------------------------------------


            if task_intent == "POLICY_QUERY":



                answer = ask_policy(

                    policy_id,

                    normalize_query(task_query)

                )



                responses.append(

                    f"""
Policy Answer:

{answer}
"""
                )






            # -------------------------------------------
            # CREATE CLAIM
            # -------------------------------------------


            elif task_intent == "CREATE_CLAIM":



                incident_type = detect_incident_type(
                    task_query
                )



                if incident_type:



                    conversation_state[session_id] = {


                        "action":
                        "CREATE_CLAIM",


                        "step":
                        "WAITING_FOR_DESCRIPTION",


                        "incident_type":
                        incident_type

                    }



                    responses.append(

                        f"""
Claim creation started.

Incident Type:
{incident_type}


Please provide a brief description of the incident.
"""
                    )



                else:



                    conversation_state[session_id] = {


                        "action":
                        "CREATE_CLAIM",


                        "step":
                        "WAITING_FOR_INCIDENT_TYPE"

                    }



                    responses.append(

                        """
Please select the incident type:

1. Theft
2. Accident
3. Flood
4. Fire
5. Other
"""
                    )






            # -------------------------------------------
            # TRACK CLAIM
            # -------------------------------------------


            elif task_intent == "TRACK_CLAIM":


                import re



                match = re.search(

                    r"\d+",

                    task_query

                )



                if match:



                    claim_id = int(match.group())



                    claim = get_claim_status(
                        claim_id
                    )



                    if claim:


                        responses.append(

                            f"""
Claim Details:

Claim ID:
{claim['claim_id']}


Status:
{claim['claim_status']}


Incident:
{claim['incident_type']}


Description:
{claim['description']}
"""
                        )



                    else:


                        responses.append(

                            f"No claim found with ID {claim_id}"

                        )




        return {


            "answer":

            "\n\n".join(responses)

        }







    # ===================================================
    # SINGLE INTENT
    # ===================================================


    intent = plan[0]["intent"]




    # -----------------------------------------------
    # POLICY
    # -----------------------------------------------


    if intent == "POLICY_QUERY":



        answer = ask_policy(

            policy_id,

            normalize_query(plan[0]["query"])

        )



        return {


            "answer":
            answer

        }







    # -----------------------------------------------
    # CREATE CLAIM
    # -----------------------------------------------


    elif intent == "CREATE_CLAIM":



        incident_type = detect_incident_type(
            question
        )




        if incident_type:



            conversation_state[session_id] = {


                "action":
                "CREATE_CLAIM",


                "step":
                "WAITING_FOR_DESCRIPTION",


                "incident_type":
                incident_type

            }



            return {


                "answer":
                """
Please provide a brief description of the incident.
"""
            }






        conversation_state[session_id] = {


            "action":
            "CREATE_CLAIM",


            "step":
            "WAITING_FOR_INCIDENT_TYPE"

        }




        return {


            "answer":
            """
Please select the incident type:

1. Theft
2. Accident
3. Flood
4. Fire
5. Other

Reply with incident type.
"""
        }







    # -----------------------------------------------
    # TRACK CLAIM
    # -----------------------------------------------


    elif intent == "TRACK_CLAIM":



        import re



        match = re.search(

            r"\d+",

            question

        )



        if match:


            claim_id = int(match.group())



            claim = get_claim_status(
                claim_id
            )



            if claim:


                return {


                    "answer":
                    f"""
Claim Details:

Claim ID:
{claim['claim_id']}


Status:
{claim['claim_status']}


Incident:
{claim['incident_type']}


Description:
{claim['description']}
"""
                }





            return {


                "answer":
                f"No claim found with ID {claim_id}"

            }






        return {


            "answer":
            "Please provide a valid claim ID."

        }






    # -----------------------------------------------
    # UNKNOWN
    # -----------------------------------------------


    return {


        "answer":
        """
I could not understand your request.

You can:

• Ask policy questions
• Create a claim
• Track claim status
"""
    }