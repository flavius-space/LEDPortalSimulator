/**
 * PBMessageFactoryAPA102Data
 */
public class PBMessageFactoryAPA102Data extends PBMessageFactoryData{
	public final long freq;
	public byte brightness = 0x1f;
	public PBMessageFactoryAPA102Data(final PBColorOrder colorOrder, int channel, long freq) {
		super(PBRecordType.SET_CHANNEL_APA102_DATA, channel, 8, colorOrder);
		this.freq = freq;
	}
	@Override
	protected int writeBody(byte[] message, int offset, int[] colorIndices, int[] colors) {
		this.validate(colorIndices);
		int i=offset;
		if (debug) System.out.printf("freq: 0x%08x (%dd)\n", this.freq, this.freq);
		for(byte b : LPByteUtils.uint32LEBytes(this.freq)) {
			message[i++] = b;
		}
		if (debug) System.out.printf("colorOrders: 0x%02x \n", this.colorOrder.colorOrder);
		message[i++] = (byte) this.colorOrder.colorOrder;
		if (debug) System.out.printf("struct padding: 0x00 \n");
		message[i++] = 0x00;
		if (debug) System.out.printf("pixels: 0x%04x (%dd)\n", colorIndices.length, colorIndices.length);
		for(byte b : LPByteUtils.uint16LEBytes(colorIndices.length)) {
			message[i++] = b;
		}
		if (debug) System.out.printf("global brightness: 0x%02x\n", brightness);
		for(int colorIdx : colorIndices) {
			int c = 0;
			for(byte b : this.colorOrder.colorBytes(colors[colorIdx])) {
				message[i++] = b;
				// overwrite the 4th byte with the brightness register
				if(c == 3) message[i-1] = this.brightness;
				c++;
			}
		}
		return (i - offset);
	}
	@Override
	public int bufferSpace(int[] colorIndices) {
		return 4 * (colorIndices.length + 2);
	}
	@Override
	public void validate(int[] colorIndices) throws RuntimeException {
		if (this.bufferSpace(colorIndices) > bytesPerChannel) {
			throw new RuntimeException(
				"too many pixels for a single channel! colorIndices.length="
				+ String.valueOf(colorIndices.length) + "; colorSize="
				+ String.valueOf(this.colorSize) + "; bytesPerChannel="
				+ String.valueOf(bytesPerChannel)
			);
		}
		if (this.colorOrder.numElements != 4) {
			throw new RuntimeException(
				"APA102-Type leds must have a colorOrder of length 4, e.g. RGBV. Instead found"
				+ String.valueOf(this.colorOrder.numElements) + ", " + this.colorOrder.name()
			);
		}
	}
}
