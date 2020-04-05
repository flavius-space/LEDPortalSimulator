/**
 * PBMessageFactoryData
 */
public abstract class PBMessageFactoryData extends PBMessageFactory{
	public final PBColorOrder colorOrder;
	public static final int bytesPerChannel = 2048;
	public PBMessageFactoryData(PBRecordType recordType, int channel, int baseSize, PBColorOrder colorOrder) {
		super(recordType, channel, baseSize, colorOrder.numElements);
		this.colorOrder = colorOrder;
		if (debug) System.out.printf("colorOrder: %s\n", this.colorOrder.name());
	}
	/**
	 * Calculate the number of bytes required to store these colors on the PixelBlaze buffer.
	 *
	 * Override in subclasses.
	 * @return
	 */
	public int bufferSpace(int[] colorIndices) {
		return this.colorSize * colorIndices.length;
	}
	public void validate(int[] colorIndices) throws RuntimeException {
		if (this.bufferSpace(colorIndices) > bytesPerChannel) {
			throw new RuntimeException(
				"too many pixels for a single channel! colorIndices.length="
				+ String.valueOf(colorIndices.length) + "; colorSize="
				+ String.valueOf(this.colorSize) + "; bytesPerChannel="
				+ String.valueOf(bytesPerChannel)
			);
		}
	}
}
