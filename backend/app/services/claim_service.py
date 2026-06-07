from app.database.db import get_connection


def create_claim(policy_id, incident_type, description):

    conn = get_connection()

    cursor = conn.cursor()

    query = """
    INSERT INTO claims(
        policy_id,
        incident_type,
        description,
        claim_status
    )
    VALUES(%s,%s,%s,%s)
    """

    values = (
        policy_id,
        incident_type,
        description,
        "SUBMITTED"
    )

    cursor.execute(query, values)

    conn.commit()

    claim_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return claim_id

def get_claim_status(claim_id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT *
    FROM claims
    WHERE claim_id = %s
    """

    cursor.execute(query, (claim_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result

def get_user_policies(user_id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        policy_id,
        policy_number,
        vehicle_model,
        vehicle_number,
        status
    FROM policies
    WHERE user_id = %s
    """

    cursor.execute(query, (user_id,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results


def update_claim_status(
    claim_id,
    new_status
):

    conn = get_connection()

    cursor = conn.cursor()

    query = """
    UPDATE claims
    SET claim_status = %s
    WHERE claim_id = %s
    """

    cursor.execute(
        query,
        (
            new_status,
            claim_id
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    return True