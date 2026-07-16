"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { api, type RegisterPayload } from "@/lib/api";
import { Spinner } from "@/components/loading";

export default function RegisterPage() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterPayload>();

  const password = watch("password");

  const onSubmit = async (data: RegisterPayload) => {
    try {
      await api.register(data);
      toast.success("Registration submitted! Awaiting admin approval.");
      router.push("/login");
    } catch (err: any) {
      toast.error(err.message ?? "Registration failed");
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <div className="card p-6">
        <h1 className="text-2xl font-bold">Create your account</h1>
        <p className="mt-1 text-sm text-slate-500">
          Your account will be reviewed by an admin before you can log in.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 grid gap-4 sm:grid-cols-2">
          <Field label="Student Name" error={errors.name?.message}>
            <input className="input" {...register("name", { required: "Required", minLength: { value: 2, message: "Too short" } })} />
          </Field>
          <Field label="Email" error={errors.email?.message}>
            <input type="email" className="input" {...register("email", { required: "Required" })} />
          </Field>
          <Field label="Mobile Number" error={errors.mobile?.message}>
            <input className="input" {...register("mobile", { required: "Required", pattern: { value: /^[0-9+\-\s]{7,15}$/, message: "Invalid number" } })} />
          </Field>
          <Field label="College" error={errors.college?.message}>
            <input className="input" {...register("college")} />
          </Field>
          <Field label="City" error={errors.city?.message}>
            <input className="input" {...register("city")} />
          </Field>
          <Field label="State" error={errors.state?.message}>
            <input className="input" {...register("state")} />
          </Field>
          <Field label="Password" error={errors.password?.message}>
            <input type="password" className="input" {...register("password", { required: "Required", minLength: { value: 6, message: "Min 6 characters" } })} />
          </Field>
          <Field label="Confirm Password" error={errors.confirm_password?.message}>
            <input
              type="password"
              className="input"
              {...register("confirm_password", {
                required: "Required",
                validate: (v) => v === password || "Passwords do not match",
              })}
            />
          </Field>

          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
              {isSubmitting && <Spinner />} Register
            </button>
          </div>
        </form>

        <p className="mt-4 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-brand-600 hover:underline">Login</Link>
        </p>
      </div>
    </div>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
