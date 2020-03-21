import java.util.ArrayList;
import java.util.List;
import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

public class LPStructure {
	public String type;
	public List<PVector> vertices;
	public List<int[]> edges;
	public List<int[]> faces;
	public PMatrix3D matrix;
	public LPStructure() {
		vertices = new ArrayList<PVector>();
		edges = new ArrayList<int[]>();
		faces = new ArrayList<int[]>();
	}

    public LPStructure updateFromJSONObject(JSONObject structureConfig) {
		if(structureConfig.hasKey("type")) {
			this.type = structureConfig.getString("type");
		}
		if(structureConfig.hasKey("vertices")) {
            JSONArray vertexList = structureConfig.getJSONArray("vertices");
            for(int i = 0; i < vertexList.size(); i++) {
				JSONArray vertex = vertexList.getJSONArray(i);
                this.vertices.add(new PVector(vertex.getFloat(0), vertex.getFloat(1), vertex.getFloat(2)));
            }
		}
		if(structureConfig.hasKey("matrix")) {
			JSONArray matrix = structureConfig.getJSONArray("matrix");
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
		if(structureConfig.hasKey("edges")) {
            JSONArray edgeList = structureConfig.getJSONArray("edges");
            for(int i = 0; i < edgeList.size(); i++) {
				JSONArray edge = edgeList.getJSONArray(i);
                this.edges.add(edge.getIntArray());
            }
		}
		if(structureConfig.hasKey("faces")) {
            JSONArray faceList = structureConfig.getJSONArray("faces");
            for(int i = 0; i < faceList.size(); i++) {
				JSONArray face = faceList.getJSONArray(i);
                this.edges.add(face.getIntArray());
            }
		}

        return this;
    }

}
