
export default function Failed({reason="im not sure", regen_allowed=true, regen=null}){
	
	return (
		<div className="min-w-64 w-max bg-white h-18 p-2 rounded-xl shadow-xl border-[#b8c4ff] border ">
		<div className="flex items-center gap-4">
			<div>
			<h1 className="font-bold text-lg">oopsie woopsie something went wrong</h1>
			<p className="text-gray-600 ">reason: {reason}</p>
			</div>
		{regen_allowed && <button className="w-18 h-8 rounded-lg m-2 bg-white border border-[#b8c4ff] hover:bg-gray-200 transition cursor-pointer" onClick={()=>{
			regen()
		}}>retry</button>}
		</div>

		</div>
	)

}
