from jarvis.simulation.certifier import SimulationCertifier


def test_simulation_certifier_builds_certificate():
    certifier = SimulationCertifier(default_hazards=["numerical_instability"])
    cert = certifier.certify(
        sim_id="sim-1",
        model_id="model-x",
        assumptions=["a1"],
        boundary_conditions={"temp": 42},
        confidence_interval=(0.1, 0.9),
    )
    assert cert.sim_id == "sim-1"
    assert "numerical_instability" in cert.hazard_flags
    assert cert.confidence_interval == (0.1, 0.9)
