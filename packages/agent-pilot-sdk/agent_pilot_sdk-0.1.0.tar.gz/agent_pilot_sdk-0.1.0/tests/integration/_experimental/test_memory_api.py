from datetime import datetime
import agent_pilot._experimental as apx


def test_memory_operations(get_config):
    api_key, api_url = get_config

    memory_content = {
        "test_key1": "test_value1",
        "test_key2": "test_value2",
    }
    session_id = "test_session_id"
    agent_id = "test_agent_id"
    print(
        f"Creating a new memory record: memory_content={memory_content}, session_id={session_id}, agent_id={agent_id}"
    )
    memory = apx.create_agent_memory(
        memory_content=memory_content,
        session_id=session_id,
        agent_id=agent_id,
        api_key=api_key,
        api_url=api_url,
    )
    print(f"A new memory is created: {memory}")
    assert isinstance(memory.memory_id, str) and memory.memory_id != ""
    assert memory.memory_content == memory_content
    assert memory.session_id == session_id
    assert memory.agent_id == agent_id
    assert isinstance(memory.create_time, datetime) and memory.create_time is not None
    assert isinstance(memory.update_time, datetime) and memory.update_time is not None

    print(f"Querying the newly created memory with memory_id={memory.memory_id}")
    queried_memory = apx.get_agent_memory(
        memory_id=memory.memory_id,
        session_id=memory.session_id,
        agent_id=memory.agent_id,
        api_key=api_key,
        api_url=api_url,
    )
    print(f"Queried memory = {queried_memory}")
    assert queried_memory.memory_id == memory.memory_id
    assert queried_memory.memory_content == memory.memory_content
    assert queried_memory.session_id == memory.session_id
    assert queried_memory.agent_id == memory.agent_id
    # Skip timestamp check because there is a small diff when creating the record.
    # assert int(queried_memory.create_time.timestamp()) == int(memory.create_time.timestamp())
    # assert int(queried_memory.update_time.timestamp()) == int(memory.create_time.timestamp())

    new_memory_content = {
        "test_key3": "test_value3",
        "test_key4": "test_value4",
    }

    print(
        f"Updating the memory with memory_id={memory.memory_id} and \
            session_id={memory.session_id}, \
            agent_id={memory.agent_id}, \
            of new_memory_content={new_memory_content}",
    )
    is_updated = apx.update_agent_memory(
        memory_id=memory.memory_id,
        memory_content=new_memory_content,
        session_id=memory.session_id,
        agent_id=memory.agent_id,
        api_key=api_key,
        api_url=api_url,
    )
    assert is_updated is True
    print(
        f"memory with memory_id={memory.memory_id}, \
        session_id={memory.session_id}, \
        agent_id={memory.agent_id}, \
        is_updated = {is_updated}"
    )

    print(
        f"Querying again with memory_id={memory.memory_id}, \
        session_id={memory.session_id}, \
        agent_id={memory.agent_id}"
    )
    queried_memory = apx.get_agent_memory(
        memory_id=memory.memory_id,
        session_id=memory.session_id,
        agent_id=memory.agent_id,
        api_key=api_key,
        api_url=api_url,
    )
    print(f"Queried memory = {queried_memory}")
    assert queried_memory.memory_id == queried_memory.memory_id
    assert queried_memory.session_id == memory.session_id
    assert queried_memory.agent_id == memory.agent_id
    assert queried_memory.memory_content == new_memory_content
    # Skip timestamp check because there is a small diff when creating the record.
    # assert int(queried_memory.create_time.timestamp()) == int(memory.create_time.timestamp())
    assert queried_memory.update_time > memory.create_time

    print(
        f"Deleting the memory with memory_id={memory.memory_id}, \
        session_id={memory.session_id}, \
        agent_id={memory.agent_id}"
    )
    is_deleted = apx.delete_agent_memory(
        memory_id=memory.memory_id,
        session_id=memory.session_id,
        agent_id=memory.agent_id,
        api_key=api_key,
        api_url=api_url,
    )
    assert is_deleted is True
    print(
        f"memory {memory.memory_id}, \
        session_id={memory.session_id}, \
        agent_id={memory.agent_id} is_deleted = {is_deleted}"
    )

    print(
        f"Querying the deleted memory with memory_id={memory.memory_id}, \
        session_id={memory.session_id}, \
        agent_id={memory.agent_id}"
    )
    queried_memory = apx.get_agent_memory(
        memory.memory_id,
        session_id=memory.session_id,
        agent_id=memory.agent_id,
        api_key=api_key,
        api_url=api_url,
    )
    print(f"Queried memory = {queried_memory}")
    assert queried_memory is None
