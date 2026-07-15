import { useRef, useEffect, useState } from "react"
export default function Background({expanded}){
	const [number, setNumber] = useState(0)
	const items = []
	for(let i=0; i<number;i++){
		items.push(0)
	}

	const divRef = useRef()
	useEffect(()=>{
		const observer = new ResizeObserver((entries)=>{
			setNumber(Math.round(entries[0].contentRect.width/56))

		})
		observer.observe(divRef.current)

	},[])


	return(
		<div ref={divRef} className="overflow-hidden h-full w-full flex shrink-0 absolute z-0 ">
			{items.map((_,i)=>(
				<div key={i} className={`h-screen w-1  rotate-12 mr-14 shrink-0  bg-gradient ${expanded ? "bg-gradient-active" : ""}`}>
				</div>
			))}
		</div>
	)
}

