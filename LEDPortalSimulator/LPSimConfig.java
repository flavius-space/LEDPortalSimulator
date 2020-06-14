import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

import processing.data.JSONObject;
import processing.data.JSONArray;
import processing.core.PMatrix3D;
import processing.core.PVector;

public class LPSimConfig {
	private static final Logger logger = Logger.getLogger(LPMeshable.class.getName());
    public List<LPPanel> panels = new ArrayList<LPPanel>();
    public List<LPStructure> structures = new ArrayList<LPStructure>();
    public List<LPStructure> debugStructures = new ArrayList<LPStructure>();
    // public float ledSize = (float)1.0;
    public LPSimConfig () {}
    public void updateFromJSONObject(JSONObject jsonConfig) throws RuntimeException{
        // if(jsonConfig.hasKey("ledSize")) {
        //     this.ledSize = jsonConfig.getFloat("ledSize");
        // }
        if(jsonConfig.hasKey("panels")) {
            JSONArray panelList = jsonConfig.getJSONArray("panels");
            for(int i = 0; i < panelList.size(); i++) {
				LPPanel panel = new LPPanel();
                this.panels.add(panel.updateFromJSONObject(panelList.getJSONObject(i)));
            }
        }
        if(jsonConfig.hasKey("structures")) {
            JSONArray structureList = jsonConfig.getJSONArray("structures");
            for(int i = 0; i < structureList.size(); i++) {
				LPStructure structure = new LPStructure();
                this.structures.add(structure.updateFromJSONObject(structureList.getJSONObject(i)));
            }
        }
	}

	public PVector getWorldCentroid() {
		List<PVector> centroids = new ArrayList<PVector>();
		for(LPPanel panel : this.panels) {
			centroids.add(panel.getWorldCentroid());
		}
		return LPMeshable.getCentroid(centroids);
	}

	public PVector getWorldNormal() {
		List<PVector> normals = new ArrayList<PVector>();
		for(LPPanel panel : this.panels) {
			normals.add(panel.getWorldNormal());
		}
		return LPMeshable.getCentroid(normals);
	}

	public PMatrix3D getWorldFlattener() {
		PVector centroid = getWorldCentroid();
		PVector normal = getWorldNormal();
		PMatrix3D flattener = LPMeshable.getFlattener(centroid, normal);
		return flattener;
	}

	public PMatrix3D getWorldUnFlattener() {
		PVector centroid = getWorldCentroid();
		PVector normal = getWorldNormal();
		PMatrix3D flattener = LPMeshable.getUnFlattener(centroid, normal);
		return flattener;
	}

	/**
	 * Flatten the panels in the model, and determine the bounds in the x and y axes
	 * @return
	 */
	public float[][] getModelFlattenedBounds() {
		PMatrix3D flattener = getWorldFlattener();

		float[][] axisBounds = new float[][]{
			new float[]{Float.MAX_VALUE, Float.MIN_VALUE},
			new float[]{Float.MAX_VALUE, Float.MIN_VALUE}
		};

		List<PVector> modelFlattenedPoints = new ArrayList<PVector>();

		for(LPPanel panel : panels) {
			for(PVector vertex: panel.getWorldVertices()) {
				modelFlattenedPoints.add(LPMeshable.coordinateTransform(flattener, vertex));
			}
		}

		logger.info(String.format(
			"flattened points: %s", LPMeshable.formatPVectorList(modelFlattenedPoints)));

		return LPMeshable.getAxisBounds(modelFlattenedPoints);
	}
}
