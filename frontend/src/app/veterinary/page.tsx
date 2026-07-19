import { InstituteModule } from "@/components/institute-module";

export default function VeterinaryPage() {
  return (
    <InstituteModule
      moduleKey="veterinary"
      title="Veterinary Prediction"
      subtitle="Enter your marks or rank, pick a category (and state, optionally), and see probable B.V.Sc & A.H colleges."
      scoreLabel="Marks"
      scoreInputLabel="Marks (0-720)"
      rankLabel="Rank"
      rankInputLabel="Rank"
      degreeHeader="Course"
      rankHeader="Rank"
      scoreHeader="Marks"
    />
  );
}
