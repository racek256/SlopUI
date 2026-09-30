import { useRef, useEffect, useState } from "react"
export default function Background({expanded}){
	const [number, setNumber] = useState(0)
	const items = []
	for(let i=0; i<number;i++){
		items.push(0)
	}

	const divRef = useRef()

	useEffect(() => {
	  let t
	  const observer = new ResizeObserver(([entry]) => {
		const n = Math.round(entry.contentBoxSize[0].inlineSize / 60)
		if (n <= 0) return
		clearTimeout(t)
		t = setTimeout(() => setNumber(n), 120) // or setNumber(prev => n !== prev ? n : prev)
	  })
	  observer.observe(divRef.current)
	  return () => { clearTimeout(t); observer.disconnect() }
	}, [])


	return(
		<div ref={divRef} className="overflow-hidden h-full w-full flex shrink-0 absolute z-0 ">
			{items.map((_,i)=>(
				<div key={i} className={`h-[101vh] w-1  rotate-12 mr-14 shrink-0  bg-gradient ${expanded ? "bg-gradient-active" : ""}`}>
				</div>
			))}
		</div>
	)
}

