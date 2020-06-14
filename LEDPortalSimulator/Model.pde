import java.util.List;

public static class LEDPanelFixture extends LXAbstractFixture {
	public LEDPanelFixture(LPPanel panel) {
		for (PVector led : panel.getWorldPixels()) {
			addPoint(new LXPoint(led.x, led.y, led.z));
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
