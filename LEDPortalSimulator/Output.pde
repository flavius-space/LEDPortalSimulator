import java.util.Arrays;
import processing.serial.*;

static abstract class LPSerialOutput extends LXOutput {
	public static final boolean debug = true;
	public Serial port;

	public LPSerialOutput(LX lx, PApplet parent, String serialPort, int baudRate) {
		super(lx, serialPort);
		port = new Serial(parent, serialPort, baudRate);
	}

	public void write(byte[] message) {
		int i = 0;
		for (byte b: message) {
			if (debug) System.out.printf("message[%03d] = 0x%02x\n", i++, b);
		}
		this.port.write(message);
	}
}

// TODO: upgrade to the latest LX way of doing things when it's released
public static int[] allPoints(LX lx) {
	int[] points = new int[lx.total];
	for (int i = 0; i < points.length; ++i) {
		points[i] = i;
	}
	return points;
}

public class PixelBlazeExpanderOutput extends LPSerialOutput {

	public final PBMessageFactory msgFactory;
	public final PBMessageFactory drawAllFactory;
	public int channelNumber=0;
	public int[] colorIndices;

	public PixelBlazeExpanderOutput(LX lx, PApplet parent, String serialPort, int[] colorIndices) {
		super(lx, parent, serialPort, 2000000);
		this.colorIndices = colorIndices;
		// TODO: configure channel, protocol
		this.msgFactory = new PBMessageFactoryWS281X(PBColorOrder.RGBW);
		this.drawAllFactory = new PBMessageFactoryDrawAll();
	}

	public PixelBlazeExpanderOutput(LX lx, PApplet parent, String serialPort, LXFixture fixture) {
		this(lx, parent, serialPort, LXFixture.Utils.getIndices(fixture));
	}

	public PixelBlazeExpanderOutput(LX lx, PApplet parent, String serialPort) {
		this(lx, parent, serialPort, allPoints(lx));
	}

	@Override
	protected void onSend(int[] colors) {
		this.write(this.msgFactory.getMessage(this.channelNumber, this.colorIndices, colors));
		this.write(this.drawAllFactory.getMessage());
	}
}

