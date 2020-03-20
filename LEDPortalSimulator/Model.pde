import java.util.List;

public static class LEDPanelFixture extends LXAbstractFixture {
	public LEDPanelFixture(LPPanel panel) {
		for (PVector led : panel.leds) {
			PVector local = new PVector(led.x, led.y, 0.0);
			PVector world = panel.matrix.mult(local, null);
			addPoint(new LXPoint(world.x, world.y, world.z));
		}
	}
}

public LXModel modelFromPanels(List<LPPanel> panels) {
	List<LXFixture> fixtures = new ArrayList<LXFixture>();
	for (LPPanel panel : panels) {
		fixtures.add(new LEDPanelFixture(panel));
	}
	return new LXModel(fixtures.toArray(new LXFixture[fixtures.size()]));
}
