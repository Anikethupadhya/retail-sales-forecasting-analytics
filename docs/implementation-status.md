# Implementation status

Starting revision: d18fc1fe20c3ed6b766b515694886ca01c696286. Verified default branch: main. Feature branch: feature/reproducible-training-windows. Initial working tree clean; two commits. Local checkpoint: deliverables/pre-training-windows.bundle (complete bundle verified).

| Milestone | Status | Evidence / decision |
| --- | --- | --- |
| Starting Git/runtime foundation | Verified | Two commits; Python 3.14.3; origin/main equals starting revision |
| Historical artifact checksums/results | In progress | Exact reconciliation and protected snapshot before implementation |
| Repeatable committed clean reproduction | In progress | Unique workspace, environment, reference and evidence directories |
| Database-independent CI | Missing | Build temporary database from committed aggregates |
| Protocol committed before execution | Missing | Expanding / 182 / 365; fixed cohort and model |
| Experiment and reconciliation | Missing | Same support; all failures retained |
| Dashboard and documentation | Missing | Preserve three tabs; inspectable window comparison |
| Exact-revision final verification | Missing | Commit implementation before clean run |
| Push, latest-head CI, draft PR | Missing | Keep main and private visibility unchanged |
| Review ZIP | Missing | Customer-free allowlist |

No external blocker currently established. Existing evidence remains preserved. New runs use .verification-runs/<UTC-and-UUID>, with evidence outside the tested checkout.
