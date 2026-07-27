import { InstituteModule } from "@/components/institute-module";

export default function BamsOtherStatePage() {
  return (
    <InstituteModule
      moduleKey="bams-other-state"
      title="BAMS in Other State"
      subtitle="Enter your name, marks or AIR, and pick a state (or all states) to see BAMS colleges outside Maharashtra."
      scoreLabel="Marks"
      scoreInputLabel="Marks (0-720)"
      rankLabel="All-India Rank (AIR)"
      rankInputLabel="All-India Rank"
      scoreHeader="Marks"
      rankHeader="AIR"
    />
  );
}
