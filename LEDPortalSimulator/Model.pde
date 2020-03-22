import java.util.List;

public static class LEDPanelFixture extends LXAbstractFixture {
	public LEDPanelFixture(LPPanel panel) {
		for (PVector led : panel.leds) {
			PVector world = getWorldCoordinate(panel.matrix, led);
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

public static PVector getWorldCoordinate(PMatrix3D matrix, PVector local) {
	PVector world = matrix.mult(local, null);
	return new PVector(world.x, world.z, world.y);
}
