import { ButtonHTMLAttributes } from 'react'

export function Button(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className="rounded-md bg-slate-900 px-3 py-2 text-white" {...props} />
}
