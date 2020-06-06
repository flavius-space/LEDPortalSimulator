import java.util.ArrayList;
import java.util.List;
import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

public abstract class LPMeshable {
	public List<PVector> vertices;
	public List<int[]> edges;
	public List<int[]> faces;
	public PMatrix3D matrix;
	public LPMeshable() {
		vertices = new ArrayList<PVector>();
		edges = new ArrayList<int[]>();
		faces = new ArrayList<int[]>();
	}

	public List<PVector> getWorldVertices() {
		List<PVector> worldVertices = new ArrayList<PVector>();
		for(PVector vertex : this.vertices) {
			worldVertices.add(getWorldCoordinate(this.matrix, vertex));
		}
		return worldVertices;
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

	public static PVector getWorldCoordinate(PMatrix3D matrix, PVector local) {
		PVector world = matrix.mult(local, null);
		return new PVector(world.x, world.z, world.y);
	}

    public LPMeshable updateFromJSONObject(JSONObject jsonConfig) {
		if(jsonConfig.hasKey("vertices")) {
            JSONArray vertexList = jsonConfig.getJSONArray("vertices");
            for(int i = 0; i < vertexList.size(); i++) {
				JSONArray vertex = vertexList.getJSONArray(i);
                this.vertices.add(new PVector(vertex.getFloat(0), vertex.getFloat(1), vertex.getFloat(2)));
            }
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
		}
		if(jsonConfig.hasKey("edges")) {
            JSONArray edgeList = jsonConfig.getJSONArray("edges");
            for(int i = 0; i < edgeList.size(); i++) {
				JSONArray edge = edgeList.getJSONArray(i);
                this.edges.add(edge.getIntArray());
            }
		}
		if(jsonConfig.hasKey("faces")) {
            JSONArray faceList = jsonConfig.getJSONArray("faces");
            for(int i = 0; i < faceList.size(); i++) {
				JSONArray face = faceList.getJSONArray(i);
                this.edges.add(face.getIntArray());
            }
		}

        return this;
	}
}
