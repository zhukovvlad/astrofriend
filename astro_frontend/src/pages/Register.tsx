import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, Mail, Lock, Loader2, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";

export default function Register() {
  const navigate = useNavigate();
  const { register, isLoading, error, clearError } = useAuthStore();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationError("");
    
    if (password !== confirmPassword) {
      setValidationError("Passwords don't match");
      return;
    }
    
    if (password.length < 6) {
      setValidationError("Password must be at least 6 characters");
      return;
    }
    
    try {
      await register({ email, password });
      navigate("/dashboard");
    } catch {
      // Error handled by store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 stars-bg">
      <div className="fixed inset-0 bg-linear-to-br from-background via-background to-accent/10 -z-10" />
      
      <motion.div
        className="fixed top-32 right-32 w-80 h-80 bg-accent/20 rounded-full blur-3xl"
        animate={{
          scale: [1, 1.3, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{ duration: 9, repeat: Infinity }}
      />
      <motion.div
        className="fixed bottom-32 left-32 w-64 h-64 bg-primary/20 rounded-full blur-3xl"
        animate={{
          scale: [1.2, 1, 1.2],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{ duration: 7, repeat: Infinity }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card className="w-full max-w-md glass glow-pink">
          <CardHeader className="text-center space-y-2">
            <motion.div
              className="mx-auto w-16 h-16 bg-linear-to-br from-accent to-primary rounded-2xl flex items-center justify-center mb-4"
              whileHover={{ scale: 1.1 }}
              transition={{ duration: 0.3 }}
            >
              <UserPlus className="w-8 h-8 text-white" />
            </motion.div>
            
            <CardTitle className="text-3xl font-bold text-gradient animate-gradient">
              Join the Stars
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              Create your account and find your cosmic match 🌙
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {(error || validationError) && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-3 rounded-lg bg-destructive/20 border border-destructive/50 text-destructive text-sm"
                >
                  {error || validationError}
                </motion.div>
              )}

              <div className="relative">
                <label htmlFor="email" className="sr-only">Email address</label>
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" aria-hidden="true" />
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 bg-input/50 border-border/50 focus:border-accent"
                  required
                />
              </div>

              <div className="relative">
                <label htmlFor="password" className="sr-only">Password</label>
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" aria-hidden="true" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 bg-input/50 border-border/50 focus:border-accent"
                  required
                />
              </div>

              <div className="relative">
                <label htmlFor="confirmPassword" className="sr-only">Confirm password</label>
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" aria-hidden="true" />
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="pl-10 bg-input/50 border-border/50 focus:border-accent"
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full bg-linear-to-r from-accent to-primary hover:opacity-90 transition-opacity"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Aligning the stars...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Create Account
                  </>
                )}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link
                  to="/login"
                  className="text-accent hover:text-primary transition-colors underline underline-offset-4"
                >
                  Sign in
                </Link>
              </p>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
