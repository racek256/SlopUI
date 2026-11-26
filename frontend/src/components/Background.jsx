const STRIPE = 4   // px, stripe thickness
const PITCH = 60   // px, distance between stripe starts (measured horizontally)
const TILT = 12    // degrees away from vertical, matches the old rotate-12

// A mask period is measured along the gradient axis, not across the box, so the
// wanted horizontal pitch has to be projected onto that axis (sin of the angle
// between the axis and the horizontal).
const ANGLE = 90 + TILT
const PERIOD = (PITCH * Math.sin((ANGLE * Math.PI) / 180)).toFixed(3)

const STRIPE_MASK =
	`repeating-linear-gradient(${ANGLE}deg, #000 0 ${STRIPE}px, transparent ${STRIPE}px ${PERIOD}px)`

export default function Background({ expanded }) {
	// One full-bleed element: the vertical glow gradient is painted on it and a
	// repeating mask cuts it into tilted stripes. Nothing is measured and no
	// element count is derived from the viewport, so the pattern covers the box
	// at every size, zoom level, DPR, orientation and mid-resize frame. The old
	// `width / 56` bar count could not: it ignored the lean of the rotated bars,
	// so wide boxes ran out of stripes before the right edge, and rem/vh sizing
	// drifted with root-font changes and mobile viewport quirks.
	return (
		<div
			aria-hidden="true"
			className="pointer-events-none absolute inset-0 z-0 overflow-hidden"
		>
			<div
				className={`absolute inset-0 bg-gradient ${expanded ? "bg-gradient-active" : ""}`}
				style={{ maskImage: STRIPE_MASK, WebkitMaskImage: STRIPE_MASK }}
			/>
		</div>
	)
}
