import { InstituteModule } from "@/components/institute-module";

export default function MbbsOtherStatePage() {
  return (
    <InstituteModule
      moduleKey="mbbs-other-state"
      title="MBBS in Other State"
      subtitle="Enter your marks or AIR and pick a state (or all states) to see state-quota MBBS colleges outside Maharashtra."
      scoreLabel="Marks"
      scoreInputLabel="Marks (0-720)"
      rankLabel="All-India Rank (AIR)"
      rankInputLabel="All-India Rank"
      scoreHeader="Marks"
      rankHeader="AIR"
    />
  );
}
