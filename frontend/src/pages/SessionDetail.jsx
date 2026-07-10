import React from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import api from "../services/api";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import { Loader2, XCircle, CheckCircle, AlertCircle } from "lucide-react";

export default function SessionDetail() {
  const { id } = useParams();

  // Fetch session details
  const {
    data: session,
    isLoading: sessionLoading,
    isError: sessionError,
  } = useQuery({
    queryKey: ["sessionDetail", id],
    queryFn: async () => {
      const res = await api.get(`/sessions/${id}`);
      return res.data;
    },
    enabled: !!id,
  });

  // Generate AI summary after session data is loaded
  const {
    mutate: generateSummary,
    data: summaryData,
    isPending: summaryLoading,
    isError: summaryError,
  } = useMutation({
    mutationFn: async (notes) => {
      const res = await api.post("/ai/session-summary", {
        session_notes: notes,
      });
      return res.data;
    },
  });

  // Trigger AI summary when session notes are available
  React.useEffect(() => {
    if (session?.notes) {
      generateSummary(session.notes);
    }
  }, [session]);

  if (sessionLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-accent" size={48} />
      </div>
    );
  }

  if (sessionError) {
    return (
      <div className="flex flex-col items-center justify-center text-center p-6">
        <AlertCircle className="text-danger" size={48} />
        <p className="mt-4 font-semibold text-lg">Failed to load session details.</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Session Details</h1>
      <Card className="mb-6 p-6">
        <div className="flex flex-col gap-4">
          <div>
            <span className="font-semibold">Mentor:</span> {session.mentor_name}
          </div>
          <div>
            <span className="font-semibold">Skill:</span> {session.skill_name}
          </div>
          <div>
            <span className="font-semibold">Scheduled:</span>{" "}
            {new Date(session.scheduled_at).toLocaleString()}
          </div>
          {session.meeting_link && (
            <Button
              as="a"
              href={session.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
              variant="primary"
            >
              Join Call
            </Button>
          )}
        </div>
      </Card>

      {/* Session Notes */}
      {session.notes && (
        <Card className="mb-6 p-4">
          <h2 className="text-xl font-semibold mb-2">Your Notes</h2>
          <p className="whitespace-pre-wrap text-text-secondary">{session.notes}</p>
        </Card>
      )}

      {/* AI Summary */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">AI Session Summary</h2>
        {summaryLoading && (
          <div className="flex items-center space-x-2">
            <Loader2 className="animate-spin" size={20} />
            <span>Generating summary...</span>
          </div>
        )}
        {summaryError && (
          <div className="flex items-center space-x-2 text-danger">
            <AlertCircle size={20} />
            <span>Failed to generate summary.</span>
          </div>
        )}
        {summaryData && (
          <div className="space-y-4">
            <section>
              <h3 className="font-semibold mb-1">Summary</h3>
              <p className="text-text-secondary whitespace-pre-wrap">
                {summaryData.summary}
              </p>
            </section>
            <section>
              <h3 className="font-semibold mb-1">Key Points</h3>
              <ul className="list-disc list-inside space-y-1">
                {summaryData.key_points.map((pt, idx) => (
                  <li key={idx}>{pt}</li>
                ))}
              </ul>
            </section>
            <section>
              <h3 className="font-semibold mb-1">Action Items</h3>
              <ul className="list-disc list-inside space-y-1">
                {summaryData.action_items.map((it, idx) => (
                  <li key={idx}>{it}</li>
                ))}
              </ul>
            </section>
            <section>
              <h3 className="font-semibold mb-1">Recommended Resources</h3>
              <ul className="list-disc list-inside space-y-1">
                {summaryData.recommended_resources.map((res, idx) => (
                  <li key={idx} className="text-accent underline">
                    <a href={res} target="_blank" rel="noopener noreferrer">
                      {res}
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        )}
      </Card>
    </div>
  );
}
