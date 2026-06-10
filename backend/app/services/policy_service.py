from app.database.db import get_connection


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

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def get_policy_document(policy_id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        document_id,
        policy_id,
        document_type,
        file_path,
        upload_date
    FROM policy_documents
    WHERE policy_id = %s
    """

    cursor.execute(query, (policy_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result