import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

public abstract class LPMeshable {
	private static final Logger logger = Logger.getLogger(LPMeshable.class.getName());
	public List<PVector> vertices;
	public List<int[]> edges;
	public List<int[]> faces;
	public PMatrix3D matrix;
	public String name;
	public LPMeshable() {
		vertices = new ArrayList<PVector>();
		edges = new ArrayList<int[]>();
		faces = new ArrayList<int[]>();
	}

	/**
	 * For some inexplicable reason, the coordinate system for processing UI components as
	 * the camera is oriented so that "up" is the Y-Axis, where every other animation software in
	 * the fucking world uses the Z-axis for up.
	 */
	public static final PMatrix3D worldToUI = new PMatrix3D(
		0, 1, 0, 0,
		0, 0, 1, 0,
		1, 0, 0, 0,
		0, 0, 0, 1
	);

	public static String floatFmt = "%7.3f";

	public static String formatPVector(PVector vector) {
		return String.format(
			"[" + String.join(", ", floatFmt, floatFmt, floatFmt) + "]",
			vector.x, vector.y, vector.z
		);
	}

	public static String formatPVectorList(List<PVector> vectors) {
		String output = "[";
		int size = vectors.size();
		if (size > 8) {
			for (PVector vector : vectors.subList(0, 3)) {
				output += "\n\t" + formatPVector(vector);
			}
			output += "\n\t" + "...";
			for (PVector vector : vectors.subList(size - 4, size - 1)) {
				output += "\n\t" + formatPVector(vector);
			}
		} else {
			for (PVector vector : vectors) {
				output += "\n\t" + formatPVector(vector);
			}
		}
		return output + "\n]";
	}

	public static String formatPMatrix3D(PMatrix3D matrix) {
		return String.format(
			String.format("["
			+ "\n\t[%1$s, %1$s, %1$s, %1$s]"
			+ "\n\t[%1$s, %1$s, %1$s, %1$s]"
			+ "\n\t[%1$s, %1$s, %1$s, %1$s]"
			+ "\n\t[%1$s, %1$s, %1$s, %1$s]"
			+ "\n]", floatFmt),
			matrix.m00,
			matrix.m01,
			matrix.m02,
			matrix.m03,
			matrix.m10,
			matrix.m11,
			matrix.m12,
			matrix.m13,
			matrix.m20,
			matrix.m21,
			matrix.m22,
			matrix.m23,
			matrix.m30,
			matrix.m31,
			matrix.m32,
			matrix.m33
		);
	}

	public List<PVector> getWorldVertices() {
		List<PVector> worldVertices = new ArrayList<PVector>();
		for(PVector vertex : this.vertices) {
			worldVertices.add(getWorldCoordinate(this.matrix, vertex));
		}
		logger.info(String.format("world vertices: %s", formatPVectorList(worldVertices)));
		return worldVertices;
	}

	public static PVector getCentroid(List<PVector> points) {
		PVector result = new PVector(0, 0, 0);
		for(PVector point : points) {
			result = result.add(point);
		}
		result.div(points.size());
		logger.info(String.format("centroid %s", LPMeshable.formatPVector(result)));
		return result;
	}

	public PVector getWorldCentroid() {
		return getCentroid(this.getWorldVertices());
	}

	public List<PVector[]> getWorldEdges() {
		List<PVector[]> worldEdges = new ArrayList<PVector[]>();
		for(int[] edge : this.edges) {
			PVector start = getWorldCoordinate(this.matrix, this.vertices.get(edge[0]));
			PVector end = getWorldCoordinate(this.matrix, this.vertices.get(edge[1]));
			worldEdges.add(new PVector[]{start, end});
		}
		return worldEdges;
	}

	public static PVector coordinateTransform(PMatrix3D matrix, PVector local) {
		PVector world = local;
		if (matrix != null) {
			world = matrix.mult(local, null);
		}
		return world;
	}

	public static PVector getUICoordinate(PVector world) {
		return coordinateTransform(worldToUI, world);
	}

	public static PVector getPixelCoordinate(PVector world) {
		return coordinateTransform(worldToUI, world);
	}

	public static PVector getWorldCoordinate(PMatrix3D matrix, PVector local) {
		return coordinateTransform(matrix, local);
	}

    public LPMeshable updateFromJSONObject(JSONObject jsonConfig) {
		if(jsonConfig.hasKey("name")) {
			String name = jsonConfig.getString("name");
			if(!name.equals("")) {
				logger.info(String.format("has name %s ", name));
				this.name = name;
			}
		}
		if(jsonConfig.hasKey("vertices")) {
			JSONArray vertexList = jsonConfig.getJSONArray("vertices");
            for(int i = 0; i < vertexList.size(); i++) {
				JSONArray vertex = vertexList.getJSONArray(i);
                this.vertices.add(new PVector(vertex.getFloat(0), vertex.getFloat(1), vertex.getFloat(2)));
			}
			logger.info(String.format(
				"has %d vertices: %s", this.vertices.size(), formatPVectorList(this.vertices)));
		}
		if(jsonConfig.hasKey("matrix")) {
			JSONArray matrix = jsonConfig.getJSONArray("matrix");
			this.matrix = new PMatrix3D(
				matrix.getJSONArray(0).getFloat(0),
				matrix.getJSONArray(0).getFloat(1),
				matrix.getJSONArray(0).getFloat(2),
				matrix.getJSONArray(0).getFloat(3),
				matrix.getJSONArray(1).getFloat(0),
				matrix.getJSONArray(1).getFloat(1),
				matrix.getJSONArray(1).getFloat(2),
				matrix.getJSONArray(1).getFloat(3),
				matrix.getJSONArray(2).getFloat(0),
				matrix.getJSONArray(2).getFloat(1),
				matrix.getJSONArray(2).getFloat(2),
				matrix.getJSONArray(2).getFloat(3),
				matrix.getJSONArray(3).getFloat(0),
				matrix.getJSONArray(3).getFloat(1),
				matrix.getJSONArray(3).getFloat(2),
				matrix.getJSONArray(3).getFloat(3)
			);
			logger.info(String.format("has matrix: %s", formatPMatrix3D(this.matrix)));
		}
		if(jsonConfig.hasKey("edges")) {
			JSONArray edgeList = jsonConfig.getJSONArray("edges");
			logger.info(String.format("has %d edges", edgeList.size()));
            for(int i = 0; i < edgeList.size(); i++) {
				JSONArray edge = edgeList.getJSONArray(i);
                this.edges.add(edge.getIntArray());
            }
		}
		if(jsonConfig.hasKey("faces")) {
			JSONArray faceList = jsonConfig.getJSONArray("faces");
			logger.info(String.format("has %d faces", faceList.size()));
            for(int i = 0; i < faceList.size(); i++) {
				JSONArray face = faceList.getJSONArray(i);
                this.edges.add(face.getIntArray());
            }
		}

        return this;
	}
}
