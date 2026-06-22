from app.services.intent_service import detect_intent


def create_plan(question):

    question = question.strip()

    separators = [
        " and ",
        " then ",
        ","
    ]

    tasks = [question]

    for sep in separators:

        if sep in question.lower():

            tasks = [
                part.strip()
                for part in question.split(sep)
                if part.strip()
            ]

            break

    plan = []

    for task in tasks:

        intent = detect_intent(task)

        plan.append(
            {
                "query": task,
                "intent": intent
            }
        )

    return plan