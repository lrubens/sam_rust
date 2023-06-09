use std::collections::HashMap;

pub enum Stream {
	i(i32),
	f(f32),
	s(String)
}

// pub add_elem(&stream : Stream) {
	
// }

trait Primitive {
    fn out_done(&self) -> bool;
    fn is_debug(&self) -> bool;
    fn valid_token(&self, element: &str, datatype: DataType) -> bool;
    fn reset(&mut self);
    fn get_done_cycle(&self) -> u64;
    fn update_done(&mut self);
    fn return_statistics(&self) -> HashMap<String, u64>;
    fn return_statistics_base(&self) -> HashMap<String, u64>;
}

impl Primitive {
    fn new(
        debug: bool,
        statistics: bool,
        name: String,
        back_en: bool,
    ) -> Self {
        Self {
            name,
            done: false,
            debug,
            done_cycles: 0,
            start_cycle: 0,
            total_cycles: 0,
            block_start: true,
            get_stats: statistics,
            backpressure_en: back_en,
        }
    }

    fn out_done(&self) -> bool {
        self.done
    }

    fn is_debug(&self) -> bool {
        self.debug
    }

    fn valid_token(&self, element: &str, datatype: DataType) -> bool {
        return element != "" && element != None && \
            (is_dtkn(element) || is_stkn(element) || is_nc_tkn(element, datatype) || is_0tkn(element))
    }

    fn reset(&mut self) {
        self.done = false;
    }

    fn get_done_cycle(&self) -> u64 {
        if self.done {
            return self.done_cycles;
        } else {
            return 0;
        }
    }

    fn update_done(&mut self) {
        self.total_cycles += 1;
        if !self.done {
            self.done_cycles += 1;
        }
        if !self.block_start && self.start_cycle == 0 {
            self.start_cycle = self.total_cycles;
        }
    }

    fn return_statistics(&self) -> HashMap<String, u64> {
        let mut stats = HashMap::new();
        stats.insert("done_cycles", self.done_cycles);
        stats.insert("start_cycle", self.start_cycle);
        stats.insert("total_cycle", self.total_cycles);
        return stats;
    }

    fn return_statistics_base(&self) -> HashMap<String, u64> {
        let mut stats = HashMap::new();
        stats.insert("done_cycles", self.done_cycles);
        stats.insert("start_cycle", self.start_cycle);
        stats.insert("total_cycle", self.total_cycles);
        return stats;
    }
}

fn remove_emptystr(stream: Vec<&str>) -> Vec<&str> {
    return stream.into_iter().filter(|x| x != "").collect();
}

fn remove_stoptkn(stream: Vec<&str>) -> Vec<&str> {
    return stream.into_iter().filter(|x| x != "S").collect();
}

fn remove_donetkn(stream: Vec<&str>) -> Vec<&str> {
    return stream.into_iter().filter(|x| x != "D").collect();
}
