import { useState } from 'react'
import Discord from '../Assets/discord.svg?react'
import Logo from '../Assets/logo.svg?react'
import { useRef } from 'react'
import Cookies from 'js-cookie'


export default function Login({ finishLogin }) {
	const demo = import.meta.env.VITE_DEMO_MODE;
	const discord_client_id = import.meta.env.DISCORD_CLIENT_ID;
	const discord_redirect_uri = import.meta.env.DISCORD_REDIRECT_URI;
	const [signup, switchsignup] = useState(false)
	const [error, setError] = useState(null)
	const username = useRef()
	const password = useRef()

	async function discordLogin(){
		console.log("discord")
	//const state = crypto.randomUUID();

		console.log("client id: "+ discord_client_id)
		console.log("redirect uri: "+ discord_redirect_uri)
	const params = new URLSearchParams({
		client_id: discord_client_id,
		response_type: "code",
		redirect_uri: discord_redirect_uri,
		scope: "identify email",
	})
	window.location.href = `https://discord.com/oauth2/authorize?${params}`
}


	return (
		<div>
			<div className="absolute z-101 w-screen  h-screen inset-0 bg-black/30 backdrop-blur-sm" />
			<div className="absolute top-1/2 left-1/2 shadow-lg bg-secondary text-text border-accent min-w-92 max-w-md  w-3/9 h-max -translate-x-1/2 -translate-y-1/2  z-101 rounded-xl flex flex-col items-center px-2 py-4 border">
				<Logo className="shadow rounded-xl w-full " />
				<div className="flex h-12 w-full mt-4">
					<div className={`flex justify-center items-center shadow grow h-full rounded-l-lg select-none cursor-pointer ${!signup && "bg-[#e1e1e1] text-black"}`} onClick={() => { switchsignup(false) }}>Sign in</div>
					<div className="bg-[#00288e] h-full w-4" />
					<div className={`flex justify-center items-center shadow grow h-full rounded-r-lg select-none cursor-pointer ${signup && "bg-[#e1e1e1] text-black"} `} onClick={() => { switchsignup(true) }}>Sign up</div>
				</div>
				{(demo && signup) ? <p className="p-6 text-xl">Signup is disabled in demo mode</p> : <div className="flex flex-col w-full">
					<input ref={username} className="border-[#c1c1c1] border rounded-lg p-2 w-full h-12 mt-4" placeholder='enter username' />
					<input ref={password} className="border-[#c1c1c1] border rounded-lg p-2 w-full h-12 mt-2" placeholder='enter password' type="password" />
					{error && <p className="self-start py-1 text-red-500 text-bold">{error}</p>}
					<button className="bg-[#00288e] hover:bg-[#10389e] transition-all cursor-pointer w-full text-white py-2 px-4 rounded-lg mt-2 h-10"
						onClick={async () => {
							let success = undefined
							if (signup) {
								success = await register(username.current.value, password.current.value)
							} else {
								success = await login(username.current.value, password.current.value)
							}
							if (success) {
								finishLogin()
							}
						}}

					>{signup ? "Create account" : "sign in"}</button></div>}

				<div className='flex w-full rounded-xl p-2.5'><div className='w-full h-1 bg-gray-400 rounded-lg'/></div>

				{discord_client_id && <div  onClick={()=>{
					console.log("discord")
					discordLogin()
				}} className='bg-[#626DED] hover:bg-[#4452BB] transition-colors w-full py-2 px-4 text-center rounded-lg cursor-pointer  text-xl text-white h-10'><p className='flex items-center justify-center gap-2 h-full'>continue with <Discord className="h-6 w-auto aspect-606/122 shrink-0" /></p></div>}
				{demo && <button className="bg-[#3f6212] hover:bg-[#4d7c0f] transition-all cursor-pointer w-full text-white py-2 px-4 rounded-lg mt-2" onClick={async () => {
					let success = undefined
					success = await login("demo", "demo")
					if (success) {
						finishLogin()
					}
				}}>Skip Login (Demo)</button>}
			</div>


		</div>
	)
}


async function login(username, password) {
	try {
		const data = await fetch(`/api/auth/login`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				username,
				password
			}),
			credentials: "include"
		})
		if (data.ok) {
			const parsed = await data.json()
			console.log(parsed)
			// Update cookie
			return true
		}
	} catch {
		return false
	}
}
async function register(username, password) {
	try {
		const data = await fetch(`/api/auth/register`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				username,
				password
			}),
			credentials: "include"
		})
		if (data.ok) {
			const parsed = await data.json()
			console.log(parsed)

			Cookies.set('token', parsed.token, { expires: 7 * 24 })
			return true
		}
	}
	catch {
		return false
	}
}

