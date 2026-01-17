import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Plus, MessageCircle, Trash2, LogOut, Sparkles, 
  Calendar, MapPin, Loader2, X 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { useBoyfriends, useCreateBoyfriend, useDeleteBoyfriend } from "@/hooks/useBoyfriends";
import { useAuthStore } from "@/stores/authStore";
import type { BoyfriendCreate } from "@/types";

const zodiacSigns = [
  "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"
];

function getZodiacSign(month: number, day: number): string {
  const dates = [20, 19, 21, 20, 21, 21, 23, 23, 23, 23, 22, 22];
  const signs = zodiacSigns;
  return day < dates[month - 1] ? signs[(month + 10) % 12] : signs[(month + 11) % 12];
}

function getRandomGradient(id: string): string {
  const gradients = [
    "from-purple-500 to-pink-500",
    "from-blue-500 to-purple-500",
    "from-pink-500 to-rose-500",
    "from-indigo-500 to-purple-500",
    "from-violet-500 to-fuchsia-500",
  ];
  const index = id.charCodeAt(0) % gradients.length;
  return gradients[index];
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { logout, user } = useAuthStore();
  const { data: boyfriends, isLoading } = useBoyfriends();
  const createBoyfriend = useCreateBoyfriend();
  const deleteBoyfriend = useDeleteBoyfriend();
  
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<BoyfriendCreate>({
    name: "",
    birth_data: {
      name: "",
      year: 1995,
      month: 1,
      day: 1,
      hour: 12,
      minute: 0,
      city: "Moscow",
      nation: "RU",
    },
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ...formData,
      birth_data: { ...formData.birth_data, name: formData.name },
    };
    await createBoyfriend.mutateAsync(data);
    setShowModal(false);
    setFormData({
      name: "",
      birth_data: { name: "", year: 1995, month: 1, day: 1, hour: 12, minute: 0, city: "Moscow", nation: "RU" },
    });
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this soulmate?")) {
      await deleteBoyfriend.mutateAsync(id);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold text-gradient">Astro-Soulmate</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground hidden sm:block">
              {user?.email}
            </span>
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold">Your Soulmates</h2>
            <p className="text-muted-foreground mt-1">
              Chat with your cosmic companions
            </p>
          </div>
          
          <Button 
            onClick={() => setShowModal(true)}
            className="bg-gradient-to-r from-primary to-accent hover:opacity-90"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create New
          </Button>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="glass">
                <CardHeader className="flex flex-row items-center gap-4">
                  <Skeleton className="w-14 h-14 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        ) : boyfriends?.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-secondary/50 flex items-center justify-center">
              <Sparkles className="w-12 h-12 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No soulmates yet</h3>
            <p className="text-muted-foreground mb-6">
              Create your first AI companion based on astrology
            </p>
            <Button 
              onClick={() => setShowModal(true)}
              className="bg-gradient-to-r from-primary to-accent"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Soulmate
            </Button>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence>
              {boyfriends?.map((bf, index) => (
                <motion.div
                  key={bf.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link to={`/chat/${bf.id}`}>
                    <Card className="glass hover:glow-purple transition-all duration-300 cursor-pointer group">
                      <CardHeader className="flex flex-row items-center gap-4">
                        <Avatar className="w-14 h-14">
                          <AvatarFallback 
                            className={`bg-gradient-to-br ${getRandomGradient(bf.id)} text-white text-xl`}
                          >
                            {getZodiacSign(bf.birth_data.month, bf.birth_data.day)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <CardTitle className="text-lg truncate group-hover:text-primary transition-colors">
                            {bf.name}
                          </CardTitle>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                            <Calendar className="w-3 h-3" />
                            <span>
                              {bf.birth_data.day}/{bf.birth_data.month}/{bf.birth_data.year}
                            </span>
                          </div>
                          {bf.birth_data.city && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <MapPin className="w-3 h-3" />
                              <span className="truncate">{bf.birth_data.city}</span>
                            </div>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent className="flex items-center justify-between pt-0">
                        <Button variant="ghost" size="sm" className="gap-2">
                          <MessageCircle className="w-4 h-4" />
                          Chat
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-muted-foreground hover:text-destructive"
                          onClick={(e) => handleDelete(bf.id, e)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </main>

      {/* Create Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => setShowModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <Card className="w-full max-w-md glass glow-purple">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-xl">Create New Soulmate</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowModal(false)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreate} className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Name</label>
                      <Input
                        placeholder="Enter a name..."
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="bg-input/50"
                        required
                      />
                    </div>
                    
                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Day</label>
                        <Input
                          type="number"
                          min="1"
                          max="31"
                          value={formData.birth_data.day}
                          onChange={(e) => setFormData({
                            ...formData,
                            birth_data: { ...formData.birth_data, day: parseInt(e.target.value) || 1 }
                          })}
                          className="bg-input/50"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Month</label>
                        <Input
                          type="number"
                          min="1"
                          max="12"
                          value={formData.birth_data.month}
                          onChange={(e) => setFormData({
                            ...formData,
                            birth_data: { ...formData.birth_data, month: parseInt(e.target.value) || 1 }
                          })}
                          className="bg-input/50"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Year</label>
                        <Input
                          type="number"
                          min="1950"
                          max="2010"
                          value={formData.birth_data.year}
                          onChange={(e) => setFormData({
                            ...formData,
                            birth_data: { ...formData.birth_data, year: parseInt(e.target.value) || 1995 }
                          })}
                          className="bg-input/50"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Hour</label>
                        <Input
                          type="number"
                          min="0"
                          max="23"
                          value={formData.birth_data.hour}
                          onChange={(e) => setFormData({
                            ...formData,
                            birth_data: { ...formData.birth_data, hour: parseInt(e.target.value) || 12 }
                          })}
                          className="bg-input/50"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Minute</label>
                        <Input
                          type="number"
                          min="0"
                          max="59"
                          value={formData.birth_data.minute}
                          onChange={(e) => setFormData({
                            ...formData,
                            birth_data: { ...formData.birth_data, minute: parseInt(e.target.value) || 0 }
                          })}
                          className="bg-input/50"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-2 block">Birth City</label>
                      <Input
                        placeholder="Moscow"
                        value={formData.birth_data.city}
                        onChange={(e) => setFormData({
                          ...formData,
                          birth_data: { ...formData.birth_data, city: e.target.value }
                        })}
                        className="bg-input/50"
                      />
                    </div>

                    <Button
                      type="submit"
                      className="w-full bg-gradient-to-r from-primary to-accent"
                      disabled={createBoyfriend.isPending}
                    >
                      {createBoyfriend.isPending ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Creating persona...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 mr-2" />
                          Create Soulmate
                        </>
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
