public class LPVideoFrame extends LXPattern {
	public String getAuthor() {
		return "Derwent McElhinney";
	}

	public LPVideoFrame(LX lx){
		super(lx);
	}

	float u;
	float v;
	int pixelValue;
	boolean firstRun = true;

	public void run(double deltaMs) {
        if (videoFrame == null) {
            return;
        }
		for (LXPoint point : model.points ) {
			PVector uiPosition = new PVector(point.x, point.y, point.z);
			PVector worldPosition = LPMeshable.pixelWorldTransform(uiPosition);
			PVector flattenedPosition = LPMeshable.coordinateTransform(flattener, worldPosition);
			u = (flattenedPosition.x - flatBounds[0][0]) / (flatBounds[0][1] - flatBounds[0][0]);
			v = (flattenedPosition.y - flatBounds[1][0]) / (flatBounds[1][1] - flatBounds[1][0]);
			pixelValue = videoFrame.get(int(videoFrame.width * u), int(videoFrame.height * v));
			if (firstRun && point.index < 10) {
				logger.info(String.format(
					"point[%d] at %s -> %s -> %s has u %7.3f , v %7.3f, %7x",
					point.index,
					LPMeshable.formatPVector(uiPosition),
					LPMeshable.formatPVector(worldPosition),
					LPMeshable.formatPVector(flattenedPosition),
					u, v, pixelValue));
			}
			setColor(point.index, pixelValue);
		}
		firstRun = false;
	}
}
