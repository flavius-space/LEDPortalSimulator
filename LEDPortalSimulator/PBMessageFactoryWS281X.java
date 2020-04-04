/**
 * PBMessageFactoryWS281X
 */
public class PBMessageFactoryWS281X extends PBMessageFactory{
	public static final boolean debug = true;
	public final PBColorOrder colorOrder;
	public static final int bytesPerChannel = 2048;
	public PBMessageFactoryWS281X(final PBColorOrder colorOrder) {
		super(PBRecordType.SET_CHANNEL_WS2812, 4, colorOrder.numElements);
		this.colorOrder = colorOrder;
	}

	@Override
	protected int writeBody(byte[] message, int offset, int[] colorIndices, int[] colors) {
		this.validate(colorIndices);
		int i=offset;
		if (debug) System.out.printf(
			"numElements: 0x%02x\ncolorOrders: 0x%02x\n",
			(byte) this.colorOrder.numElements,
			(byte) this.colorOrder.colorOrder
		);
		for(byte b : new byte[] {
			(byte) this.colorOrder.numElements,
			(byte) this.colorOrder.colorOrder
		}) {
			message[i++] = b;
		}
		if (debug) System.out.printf("pixels: 0x%04x\n", colorIndices.length);
		for(byte b : LPByteUtils.uint16LEBytes(colorIndices.length)) {
			message[i++] = b;
		}
		for(int colorIdx : colorIndices) {
			for(byte b : this.colorOrder.colorBytes(colors[colorIdx])) {
				message[i++] = b;
			}
		}
		return (i - offset);
	}
	public void validate(int[] colorIndices) throws RuntimeException {
		if (this.colorOrder.numElements * colorIndices.length > bytesPerChannel) {
			throw new RuntimeException(
				"too many pixels for a single channel! colorIndices.length="
				+ String.valueOf(colorIndices.length) + "; numElements="
				+ String.valueOf(this.colorOrder.numElements) + "; bytesPerChannel="
				+ String.valueOf(bytesPerChannel)
			);
		}
	}
}
