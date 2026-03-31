from testpaw.config import ConfigService


def test_config_service_agents_and_channels() -> None:
    service = ConfigService()
    assert service.get().app_name == "testpaw"

    service.upsert_agent("qa")
    agents = service.list_agents()
    ids = sorted(a.agent_id for a in agents)
    assert ids == ["default", "qa"]

    service.set_channels(["console"])
    assert service.get().enabled_channels == ["console"]
