
export default function Message({children, role}){
	if (role =="user"){
		return(
			<div className="border-[#b8c4ff] border bg-white w-max text-2xl rounded-2xl p-6 px-5 self-end max-w-2/3 my-2">
				
			{children}

			</div>
		)
	}else{	
		return(
			<div className="border-[#b8c4ff] border bg-white w-max text-2xl rounded-2xl p-6 px-5 self-start max-w-2/3 my-2">
				
			{children}

			</div>
		)
	}
}
