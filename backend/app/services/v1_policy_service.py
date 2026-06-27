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


def get_all_active_policy_documents():
    """Used by loader at startup to index everything."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        p.policy_id,
        p.policy_number,
        pd.file_path
    FROM policies p
    JOIN policy_documents pd ON p.policy_id = pd.policy_id
    WHERE p.status = 'ACTIVE'
    """

    cursor.execute(query)
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def get_single_policy_document(policy_id):
    """Used when a new policy is uploaded — incremental index."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        p.policy_id,
        p.policy_number,
        pd.file_path
    FROM policies p
    JOIN policy_documents pd ON p.policy_id = pd.policy_id
    WHERE p.policy_id = %s
    """

    cursor.execute(query, (policy_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result